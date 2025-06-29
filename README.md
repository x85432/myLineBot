# 開始流程
# 修改程式就可以重啟 (hot reload)
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
## 先去cmd執行
`ngrok http 5000`
會顯示
Forwarding https://abcd1234.ngrok-free.app -> http://localhost:5000
## 得到公開ip就丟到LINE developer上，修改webhook
LINE https://developers.line.biz/console/?status=success

貼
https://abcd1234.ngrok-free.app/callback


## 開始改code

## 之後可以git push到render，可以有固定ip
