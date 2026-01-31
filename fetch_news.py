def push_via_wecom(title, content, corp_id, corp_secret, agent_id, user_id):
    # 获取 access_token
    token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={corp_secret}"
    try:
        token_response = requests.get(token_url, timeout=10)
        access_token = token_response.json().get('access_token')

        if not access_token:
            print(f"获取 token 失败: {token_response.json()}")
            return False

        # 发送消息
        send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        data = {
            "touser": user_id,
            "msgtype": "markdown",
            "agentid": agent_id,
            "markdown": {
                "content": f"# {title}\n\n{content}"
            }
        }
        response = requests.post(send_url, json=data, timeout=30)
        result = response.json()

        if result.get('errcode') == 0:
            print("推送成功!")
            return True
        else:
            print(f"推送失败: {result}")
            return False
    except Exception as e:
        print(f"推送出错: {e}")
        return False
