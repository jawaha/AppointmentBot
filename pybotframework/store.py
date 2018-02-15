import redis

class SessionStore:
    def __init__(self, auth_str):
        self.auth_str = auth_str

    def get_user_data(self,channel_id,user_id):
        return None

    def get_conversation_data(self,channel_id,conversation_id):
        return None

    def get_user_conversation_data(self,conversation_id, channel_id,user_id):
        return None

    def save_user_data(self,channel_id,user_id):
        return None

    def save_conversation_data(self,channel_id,conversation_id):
        return None

    def save_user_conversation_data(self,conversation_id, channel_id,user_id):
        return None

    # Create based on class name:
    @staticmethod
    def factory(type, data, auth_str, session): #can implement this with visitor pattern so that data and session which are unused by nosqlbased could have been double dispatched
        #return eval(type + "()")
        if type == "redis": return Redis(auth_str)
        if type == "inmemory": return InMemory(data,auth_str,session)
        assert 0, "Bad store creation: " + type

class Redis(SessionStore):
    def __init__(self,auth_str):
        super(Redis, self).__init__(auth_str)
        self.redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)

    def get_user_data(self,channel_id,user_id):
        key='udata_id:'+channel_id+user_id
        return self.redis_db.sinter(key)

    def get_conversation_data(self,channel_id,conversation_id):
        key='cdata_id:'+channel_id+conversation_id
        return self.redis_db.sinter(key)

    def get_user_conversation_data(self,conversation_id, channel_id,user_id):
        key='ucdata_id:'+channel_id+conversation_id+user_id
        return self.redis_db.sinter(key)


    def save_user_data(self,channel_id,user_id,message):
        key='udata_id:'+channel_id+user_id
        self.redis_db.sadd(key, message)

    def save_conversation_data(self,channel_id,conversation_id,message):
        key='cdata_id:'+channel_id+conversation_id
        self.redis_db.sadd(key, message)

    def save_user_conversation_data(self,conversation_id, channel_id,user_id,message):
        key='ucdata_id:'+channel_id+conversation_id+user_id
        self.redis_db.sadd(key, message)

class InMemory(SessionStore):
    def __init__(self, data,auth_str,session):
        super(InMemory, self).__init__(auth_str)
        self.base_url = data["serviceUrl"]
        self.session = session
        self.etag = '*'

    def get_user_data(self,channel_id,user_id):
        transformed_url = self.base_url + \
              "/v3/botstate/{}/users/{}".format(channel_id,
                                                user_id)
        return self.get_data(transformed_url)

    def get_conversation_data(self,channel_id,conversation_id):
        transformed_url = self.base_url + \
                      "/v3/botstate/{}/conversations/{}".format(channel_id,
                                                                conversation_id)
        return self.get_data(transformed_url)

    def get_user_conversation_data(self,conversation_id, channel_id,user_id):
        transformed_url = self.base_url + \
                          "/v3/botstate/{}/conversations/{}/users/{}" \
                              .format(channel_id, conversation_id, user_id)
        return self.get_data(transformed_url)

    def get_data(self, transformed_url):
        response = self.session.get(
            url=transformed_url,
            headers={
                "Authorization": self.auth_str,
                "Content-Type": "application/json"
            }
        )
        try:
            json_data = response.json()
            data = json_data.get('data', [])
            self.etag = json_data.get('eTag')
            return data
        except:
            return None
        return

    def save_user_data(self,channel_id,user_id,message):
        transformed_url = self.base_url + \
                          "/v3/botstate/{}/users/{}".format(channel_id,
                                                            user_id)
        self.save_data(transformed_url,message)

    def save_conversation_data(self,channel_id,conversation_id,message):
        transformed_url = self.base_url + \
                          "/v3/botstate/{}/conversations/{}".format(channel_id,
                                                                    conversation_id)
        self.save_data(transformed_url,message)

    def save_user_conversation_data(self,conversation_id, channel_id,user_id,message):
        transformed_url = self.base_url + \
                          "/v3/botstate/{}/conversations/{}/users/{}" \
                              .format(channel_id, conversation_id, user_id)

        self.save_data(transformed_url,message)

    def save_data(self,trans_url,message):
        self.session.post(
            url=trans_url,
            json={"eTag": self.etag,
                  "data": message},
            headers={"Authorization": self.auth_str,
                     "Content-Type": "application/json"}
        )
