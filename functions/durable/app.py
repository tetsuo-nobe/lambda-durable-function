import random
from datetime import datetime, timedelta
from aws_durable_execution_sdk_python import (
    DurableContext,
    StepContext,
    durable_execution,
    durable_step,
)
from aws_durable_execution_sdk_python.config import (
    Duration,
    StepConfig,
    CallbackConfig,
)
from aws_durable_execution_sdk_python.retries import (
    RetryStrategyConfig,
    create_retry_strategy,
)

# Step: 利率の見積り
@durable_step
def estimate_rate(step_context: StepContext, loan_detail: dict) -> dict:
    step_context.logger.info(f"Estimate rate: {loan_detail['loan_id']}") # CloudWatch Logs のログに出力される
    #
    # 実際はここで稟議を行い利率を見積もる（ここでは割愛）
    #
    rate = 1.6
    loan_detail['estimate_rate'] = rate
    return loan_detail

# Step: 承認システムへデータを送信
@durable_step
def send_for_approval(step_context: StepContext, callback_id: str, loan_detail: dict) -> dict:
    step_context.logger.info(f"Sending load detail {loan_detail['loan_id']} for approval with callback_id: {callback_id}") # CloudWatch Logs のログに出力される
    
    # 実際はここで callback_id と申請内容を外部承認システムに送信する
    # 外部システムは 承認が完了したら callback_id を使って
    #  Lambda SendDurableExecutionCallbackSuccess API を呼び出すか
    #  SendDurableExecutionCallbackFailure API を呼び出す
    loan_detail["callback_id"] = callback_id
    loan_detail["status"] = "sent_for_approval"

    return loan_detail

# Step: 承認システムからの結果確認
@durable_step
def check_callback(step_context: StepContext, loan_detail: dict, approval_result: str) -> dict:
    step_context.logger.info(f"Approval result: {approval_result}") # CloudWatch Logs のログに出力される
    if approval_result == "Approved":
        result = "approved"
    else:
        result = "rejected"

    loan_detail["status"] = result
    return loan_detail

# Step: 結果通知処理
@durable_step
def notify_result(step_context: StepContext, loan_detail: dict) -> dict:
    step_context.logger.info(f"Notify result: {loan_detail['loan_id']}") # CloudWatch Logs のログに出力される
    timestamp = datetime.timestamp(datetime.now())
    loan_detail["status"] = "notified"
    loan_detail["timestamp"] = timestamp
    return loan_detail

# ステップの実行
@durable_execution
def lambda_handler(event: dict, context: DurableContext) -> dict:
    try:
        loan_detail = event.get("loan_detail")
        
        # ステップ 1: 利率の見積
        loan_detail_with_rate = context.step(estimate_rate(loan_detail))

        context.logger.info(f"Estimate rate: {loan_detail_with_rate['estimate_rate']}")
        
        # ステップ 2: コールバックを作成
        callback = context.create_callback(
            name="awaiting-approval",
            config=CallbackConfig(timeout=Duration.from_minutes(25))
        )
        context.logger.info(f"Created callback with id: {callback.callback_id}")
        
        # ステップ 3: callback_id を使用して承認リクエストを送信するステップを実行
        approval_request = context.step(send_for_approval(callback.callback_id, loan_detail_with_rate))
        context.logger.info(f"Approval request sent: {approval_request}") # CloudWatch Logs のログに出力される
        
        # ステップ 4: コールバックの結果を待つ
        # これは、外部システムが SendDurableExecutionCallbackSuccess または SendDurableExecutionCallbackFailure を呼び出すまでブロックされる
        approval_result = callback.result()
  
        # ステップ 5: コールバック結果確認
        callback_result = context.step(check_callback(loan_detail_with_rate, approval_result))
        if callback_result["status"] != "approved":
            raise Exception("Approval failed")  # エラー - 実行を停止

        # ステップ 6: カスタム再試行戦略による注文を処理
        retry_config = RetryStrategyConfig(max_attempts=3, backoff_rate=2.0)
        processed = context.step(
            notify_result(loan_detail_with_rate),
            config=StepConfig(retry_strategy=create_retry_strategy(retry_config)),
        )
        if processed["status"] != "notified":
            raise Exception("notification failed")  # エラー
        
        context.logger.info(f"Notification successfully processed: {processed}")
        return processed
        
    except Exception as error:
        context.logger.error(f"Error processing loan: {error}")
        raise error  # 再発生して実行を失敗させる