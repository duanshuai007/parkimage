import time
import base64
import hmac
from strictly_func_check import strictly_func_check
KEY = "WM_GROUND_LOCK"
'''
生成token
'''
@strictly_func_check
def generate_token(key:str, expire:int = 3600)->str:
    '''
        生成token
        @Args:
            key: str (用户给定的key，需要用户保存以便之后验证token,每次产生token时的key 都可以是同一个key)
            expire: int(最大有效时间，单位为s)
        @Return:
            state: str
    '''
    ts_str = str(time.time() + expire)
    ts_byte = ts_str.encode("utf-8")
    sha1_tshexstr  = hmac.new(key.encode("utf-8"),ts_byte,'sha1').hexdigest() 
    token = ts_str+':'+sha1_tshexstr
    b64_token = base64.urlsafe_b64encode(token.encode("utf-8"))
    return b64_token.decode("utf-8")

'''
验证token
'''
def certify_token(key:str, token:bytes)->bool:
    '''
        验证token
        @Args:
            key: str
            token: str
        @Returns:
            boolean
    '''
    #如果数据长度错误，则直接退出
    missing_padding = len(token) % 4
    if missing_padding != 0:
        return False
    token_str = base64.urlsafe_b64decode(token).decode('utf-8')
    token_list = token_str.split(':')
    if len(token_list) != 2:
        return False
    ts_str = token_list[0]
    if float(ts_str) < time.time():
        # token expired
        return False
    known_sha1_tsstr = token_list[1]
    sha1 = hmac.new(key.encode("utf-8"),ts_str.encode('utf-8'),'sha1')
    calc_sha1_tsstr = sha1.hexdigest()
    if calc_sha1_tsstr != known_sha1_tsstr:
        # token certification failed
        return False 
    # token certification success
    return True 

if __name__ == '__main__':
    print(generate_token(KEY, 365*24*3600))
