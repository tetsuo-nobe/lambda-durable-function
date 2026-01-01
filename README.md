# AWS Lambda Durable Function のデモ

## 前提

* 2026年1月現在、オハイオリージョンでのみ使用可能
* ランタイムは、Python 3.13 と 3.14、 Node.js 22 と 24 でのみ使用可能
* 承認用の API を発行するには boto3 で下記のバージョンが必要
  - boto3==1.42.13
  - botocore==1.42.13

---
## デモ概要 

* カーローンの利率見積りと審査を行うフローを AWS Lambda Durable Function で実装

<img width="878" height="427" alt="durable_function" src="https://github.com/user-attachments/assets/9a8d3b43-6ac5-4387-9cb6-90b0bfe8b5b1" />


---

## デモのデプロイ

1. 対象リージョンが us-east-2 になるように aws configure 等で設定する

1. AWS SAM と Docker が使用できる環境で下記を実行

    ```
    sam build --use-container
    ```

    ```
    sam deploy --guided
    ```

1. samconfig.toml で `capabilities = "CAPABILITY_NAMED_IAM"` を設定する

    ```
    [default.deploy.parameters]
    capabilities = "CAPABILITY_NAMED_IAM"
    ```

1. 再度 sam deploy を実行する

    ```
    sam deploy
    ```

---

## デモの実行

1. Durable-function は下記のようなイベントオブジェクトで実行し、フローを開始する。
    - マネジメントコンソールのテスト機能を使っても良い。
    - 実行すると、手動承認のコールバック待ちの状態になる。

    ```
    {
    "loan_detail": {
        "loan_id": "CL-1823",
        "customer_id": "CIF-9000001",
        "amount": 4000000,
        "repayment_period": 5
    }
    }
    ```


1. Durable-function 実行後、30分以内に CloudWatch Logs のログで、`Created callback with id:` のログをみつけて callback_id をメモしておく。

1. Approver-function を下記のようなイベントオブジェクトで実行し、手動承認を行いコールバックする。
    - マネジメントコンソールのテスト機能を使っても良い。
    - `xxx` の部分はメモしておいた callback_id の値に置き換える。
```
{
  "callback_id": "XXX"
}
```
1. マネジメントコンソールでのテスト結果または CloudWatch Logs のログでフローの完了を確認する。
