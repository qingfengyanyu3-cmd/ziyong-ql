import os
import json
import time
import random
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class FutianEJia:
    def __init__(self):
        # 从环境变量获取账号信息，格式为空格分隔的"账号#密码"
        self.accounts = os.environ.get('Fukuda', '').split("\n")
        # 从环境变量获取并发数，默认为1（串行执行）
        self.concurrent_workers = int(os.environ.get('FTBF', '1'))
        # 从环境变量获取是否运行发帖任务，默认为True
        self.enable_post_task = os.environ.get('FT_FT', 'True').lower() in ['true', '1', 'yes', 'on']
        self.phone = ""  # 当前处理的手机号
        self.password = ""  # 当前处理的密码
        self.memberNo = ""  # 会员编号
        self.token = ""  # 登录token
        self.uid = ""  # 用户ID
        self.memberComplexCode = ""  # 会员复杂码
        self.memberId = ""  # 会员ID
        self.notice = ""  # 通知内容
        self.base_url = "https://czyl.foton.com.cn"
        self.signed = False  # 新增签到状态
        self.pika_safe_key = None  # 皮卡生活的safeKey
        self.futian_safe_key = None  # 福田E家的safeKey
        self.notice_lock = threading.Lock()  # 用于保护notice变量的线程锁
        self.current_session_posts = []  # 记录本次运行发布的帖子ID列表

    def get_headers(self):
        """获取通用请求头"""
        return {
            'content-type': 'application/json;charset=utf-8',
            'Connection': 'Keep-Alive',
            'user-agent': 'okhttp/3.14.9',
            'Accept-Encoding': 'gzip',
        }

    def get_pk_headers(self):
        """获取皮卡生活请求头"""
        return {
            'content-type': 'application/json;charset=utf-8',
            'channel': '1',
            'Accept-Encoding': 'gzip',
        }
        
    def get_pk_auth_headers(self):
        """获取皮卡生活带认证的请求头"""
        headers = self.get_pk_headers()
        headers['token'] = self.token
        return headers
        
    def get_common_headers(self):
        """获取福田E家通用请求头"""
        return {
            'content-type': 'application/json;charset=utf-8',
            'Connection': 'Keep-Alive',
            'token': '',
            'app-key': '7918d2d1a92a02cbc577adb8d570601e72d3b640',
            'app-token': '58891364f56afa1b6b7dae3e4bbbdfbfde9ef489',
            'user-agent': 'web',
            'Accept-Encoding': 'gzip',
        }

    def login_request(self, endpoint, data):
        """登录请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, headers=self.get_headers(), data=json.dumps(data))
            time.sleep(random.randint(2, 3)) 
            return response.json()
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None

    def pk_login_request(self, endpoint, data):
        """皮卡登录请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, headers=self.get_pk_headers(), data=json.dumps(data))
            time.sleep(random.randint(2, 3)) 
            return response.json()
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None

    def common_request(self, endpoint, data):
        """通用请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            # 添加调试信息
            if 'myPost' in endpoint:
                print(f"🔍 请求URL: {url}")
                print(f"🔍 请求头: {self.get_common_headers()}")
                
            response = requests.post(url, headers=self.get_common_headers(), data=json.dumps(data))
            
            # 添加响应状态调试
            if 'myPost' in endpoint:
                print(f"🔍 响应状态码: {response.status_code}")
                print(f"🔍 响应头: {dict(response.headers)}")
                print(f"🔍 响应内容: {response.text[:500]}...")  # 只显示前500字符
                
            time.sleep(random.randint(2, 3)) 
            return response.json()
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            if 'myPost' in endpoint:
                print(f"🔍 请求异常详情: {str(e)}")
            return None

    def pk_request(self, endpoint, data):
        """皮卡请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, headers=self.get_pk_auth_headers(), data=json.dumps(data))
            time.sleep(random.randint(2, 3)) 
            return response.json()
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None

    def text_get(self):
        """获取随机文本"""
        url = "https://api.btstu.cn/yan/api.php"
        try:
            response = requests.get(url)
            time.sleep(random.randint(2, 3)) 
            return response.text
        except Exception as e:
            print(f"❌ 获取文本失败: {e}")
            return None

    def get_safe_enc(self):
        """获取皮卡生活安全加密参数"""
        if self.pika_safe_key is None:
            # 如果没有获取到safeKey，使用默认值
            return int(datetime.now().timestamp() * 1000) - 1011010100
        return int(datetime.now().timestamp() * 1000) - self.pika_safe_key

    def get_safe_enc_share(self):
        """获取福田E家分享安全加密参数"""
        if self.futian_safe_key is None:
            # 如果没有获取到safeKey，使用默认值
            return int(datetime.now().timestamp() * 1000) - 2022020200
        return int(datetime.now().timestamp() * 1000) - self.futian_safe_key
    
    def get_safe_enc_post(self):
        """获取发帖安全加密参数"""
        if self.futian_safe_key is None:
            # 如果没有获取到safeKey，使用默认值
            return int(datetime.now().timestamp() * 1000) - 20220000
        return int(datetime.now().timestamp() * 1000) - self.futian_safe_key

    def load_account_cache(self):
        """加载账号缓存信息"""
        cache_file = "ftej_info.json"
        try:
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    return cache_data
            return {}
        except Exception as e:
            print(f"❌ 读取账号缓存失败: {e}")
            return {}

    def save_account_cache(self, cache_data):
        """保存账号缓存信息"""
        cache_file = "ftej_info.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            #print("✅ 账号信息已缓存")
        except Exception as e:
            print(f"❌ 保存账号缓存失败: {e}")

    def get_pika_safe_key(self):
        """获取皮卡生活safeKey"""
        data = {
            "deviceType": 1
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/ehomes-new/pkHome/version/getVersion",
                headers=self.get_pk_headers(),
                data=json.dumps(data)
            )
            time.sleep(random.randint(2, 3)) 
            result = response.json()
            
            if result.get('code') == 200:
                self.pika_safe_key = int(result['data']['safeKey']) 
                print(f"✅ 取皮卡生活safeKey成功: {self.pika_safe_key}")
                return True
            else:
                print(f"❌ 获取皮卡生活safeKey失败: {result.get('msg', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 获取皮卡生活safeKey请求失败: {e}")
            return False
    
    def get_futian_safe_key(self):
        """获取福田E家safeKey"""
        #print("🔍 获取福田E家safeKey")
        
        try:
            import base64
            from Crypto.Cipher import DES3
            
            request_data = {
                "limit": {
                    "auth": "null",
                    "uid": "",
                    "userType": "61"
                },
                "param": {
                    "deviceType": "1",
                    "version": "7.5.1",
                    "versionCode": "345"
                }
            }
            
            key = base64.b64decode("Zm9udG9uZS10cmFuc0BseDEwMCQjMzY1")  # fontone-trans@lx100$#365
            iv = base64.b64decode("MjAxNjEyMDE=")  # 20161201
            
            cipher = DES3.new(key, DES3.MODE_CBC, iv)
            json_str = json.dumps(request_data, separators=(',', ':'))
            
            from Crypto.Util.Padding import pad
            padded_data = pad(json_str.encode('utf-8'), DES3.block_size)
            encrypted = cipher.encrypt(padded_data)
            encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
            
            headers = {
                'encrypt': 'yes',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Connection': 'Keep-Alive',
                'User-Agent': 'okhttp/3.14.9',
                'Accept-Encoding': 'gzip'
            }
            
            import urllib.parse
            post_data = f"jsonParame={urllib.parse.quote(encrypted_b64)}"
            
            response = requests.post(
                f"{self.base_url}/est/getVersion.action",
                headers=headers,
                data=post_data,
                timeout=15
            )
            time.sleep(random.randint(2, 3))  # 随机等待3-8秒
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            encrypted_response = base64.b64decode(response.text)
            decipher = DES3.new(key, DES3.MODE_CBC, iv)

            from Crypto.Util.Padding import unpad
            decrypted_padded = decipher.decrypt(encrypted_response)
            decrypted_data = unpad(decrypted_padded, DES3.block_size).decode('utf-8')
            
            result = json.loads(decrypted_data)
            
            if result.get('code') == 0:
                data_content = json.loads(result['data'])
                self.futian_safe_key = int(data_content['safeKey'])
                print("————————————————")
                print(f"✅ 取福田E家safeKey成功: {self.futian_safe_key}")
                return True
            else:
                raise Exception(f"API返回错误: {result.get('msg', '未知错误')}")
                
        except ImportError:
            print("⚠️ 缺少加密库 pycryptodome,请先安装依赖！")
        except Exception as e:
            print(f"⚠️ 获取福田E家safeKey失败: {e}")
        
        return True

    def get_share_safe_key(self):
        """获取分享任务专用的safeKey"""
        #print("🔍 获取分享任务safeKey")
        
        try:
            headers = {
                'Host': 'finance.foton.com.cn',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
                'Content-Length': '0',
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) ftejIOS',
                'Connection': 'keep-alive'
            }
            
            response = requests.post(
                "https://finance.foton.com.cn/FONTON_PROD/ehomes-new/ehomesService//api/safeH5/getSafeInfo",
                headers=headers
            )
            time.sleep(random.randint(2, 3)) 
            
            result = response.json()
            
            if result.get('code') == 200 and result.get('data'):
                share_safe_key = int(result['data']['key'])  # 确保转换为整数
                #print(f"✅ 获取分享任务safeKey成功: {share_safe_key}")
                return share_safe_key
            else:
                #print(f"❌ 获取分享任务safeKey失败: {result.get('msg', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"❌ 获取分享任务safeKey请求失败: {e}")
            return None

    def pika_login(self):
        """皮卡生活登录"""
        print('🔑 皮卡生活登录')
        
        # 加载账号缓存信息
        account_cache = self.load_account_cache()
        
        # 检查当前账号是否有缓存
        if self.phone in account_cache:
            print("🔍 发现账号缓存信息，尝试验证缓存凭证有效性")
            cache_info = account_cache[self.phone]
            
            # 加载缓存的登录信息
            cached_uid = cache_info.get("uid", "")
            cached_memberComplexCode = cache_info.get("memberComplexCode", "")
            cached_memberId = cache_info.get("memberId", "")
            cached_token = cache_info.get("token", "")
            
            # 验证缓存数据完整性
            if not all([cached_uid, cached_memberComplexCode, cached_memberId, cached_token]):
                print("❌ 缓存数据不完整，将进行重新登录")
            else:
                # 临时设置缓存的登录信息进行验证
                self.uid = cached_uid
                self.memberComplexCode = cached_memberComplexCode
                self.memberId = cached_memberId
                self.token = cached_token
                
                # 尝试签到来测试缓存的token是否有效
                data = {
                    "memberId": self.memberComplexCode,
                    "memberID": self.memberId,
                    "mobile": self.phone,
                    "token": "7fe186bb15ff4426ae84f300f05d9c8d",
                    "vin": "",
                    "safeEnc": self.get_safe_enc()
                }
                
                try:
                    pk_sign = self.pk_request('/ehomes-new/pkHome/api/bonus/signActivity2nd', data)
                    
                    # 更严格的验证：检查返回码和数据结构
                    if (pk_sign and 
                        isinstance(pk_sign, dict) and 
                        pk_sign.get('code') == 200 and 
                        'data' in pk_sign and 
                        pk_sign['data'] is not None):
                        
                        print("✅ 缓存凭证验证成功")
                        
                        # 处理签到结果
                        if pk_sign['data'].get('integral'):
                            print(f"✅ 签到成功，获得{pk_sign['data']['integral']}积分")
                        else:
                            print(f"ℹ️ 签到结果: {pk_sign['data'].get('msg', '未知')}")
                            
                        # 标记已完成签到任务
                        self.signed = True
                        return True
                    else:
                        print("❌ 缓存凭证验证失败，将进行重新登录")
                        # 清理无效的缓存数据
                        if self.phone in account_cache:
                            del account_cache[self.phone]
                            self.save_account_cache(account_cache)
                            print("🗑️ 已清理无效缓存")
                        
                except Exception as e:
                    print(f"❌ 缓存凭证验证异常: {e}，将进行重新登录")
                    # 清理可能损坏的缓存数据
                    if self.phone in account_cache:
                        del account_cache[self.phone]
                        self.save_account_cache(account_cache)
                        print("🗑️ 已清理异常缓存")
        
        
        # 重置登录信息
        self.uid = ""
        self.memberComplexCode = ""
        self.memberId = ""
        self.token = ""
        self.signed = False
        
        data = {
            "memberId": "",
            "memberID": "",
            "mobile": "",
            "token": "7fe186bb15ff4426ae84f300f05d9c8d",
            "vin": "",
            "safeEnc": self.get_safe_enc(),
            "name": self.phone,
            "password": self.password,
            "position": "",
            "deviceId": "",
            "deviceBrand": "",
            "brandName": "",
            "deviceType": "0",
            "versionCode": "21",
            "versionName": "V1.1.10"
        }
        
        try:
            pk_login = self.pk_login_request('/ehomes-new/pkHome/api/user/getLoginMember2nd', data)
            
            if not pk_login or pk_login.get('code') != 200:
                print(f"❌ 账号登录失败: {pk_login.get('msg') if pk_login else '未知错误'}")
                return False
            
            # 验证登录响应数据完整性
            if not (pk_login.get('data') and 
                    pk_login['data'].get('user') and 
                    pk_login['data']['user'].get('memberNo') and
                    pk_login['data'].get('memberComplexCode') and
                    pk_login['data'].get('token')):
                print("❌ 登录响应数据不完整")
                return False
            
            # 设置必要参数
            self.uid = pk_login['data']['user']['memberNo']
            self.memberComplexCode = pk_login['data']['memberComplexCode']
            self.memberId = pk_login['data']['user']['memberNo']
            self.token = pk_login['data']['token']
            
            # 重新加载缓存（可能被其他线程修改）
            account_cache = self.load_account_cache()
            
            # 将账号信息保存到缓存
            account_cache[self.phone] = {
                "uid": self.uid,
                "memberComplexCode": self.memberComplexCode,
                "memberId": self.memberId,
                "token": self.token,
                "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.save_account_cache(account_cache)
            
            print(f"✅ 重新登录成功并已更新缓存")
            
            # 标记尚未完成签到任务
            self.signed = False
            return True
            
        except Exception as e:
            print(f"❌ 登录过程发生异常: {e}")
            return False

    def pika_sign(self):
        """皮卡生活签到"""
        # 如果在登录时已经完成了签到，则不需要再次签到
        if hasattr(self, 'signed') and self.signed:
            print('✅ 已在登录时完成签到')
            return
        
        print('🔑 执行皮卡生活签到')
        data = {
            "memberId": self.memberComplexCode,
            "memberID": self.memberId,
            "mobile": self.phone,
            "token": "7fe186bb15ff4426ae84f300f05d9c8d",
            "vin": "",
            "safeEnc": self.get_safe_enc()
        }
        
        pk_sign = self.pk_request('/ehomes-new/pkHome/api/bonus/signActivity2nd', data)
        
        if pk_sign and 'data' in pk_sign:
            if pk_sign['data'].get('integral'):
                print(f"✅ 签到成功，获得{pk_sign['data']['integral']}积分")
            else:
                print(f"ℹ️ 签到结果: {pk_sign['data'].get('msg', '未知')}")
        else:
            print(f"❌ 签到失败")

    def futian_login(self):
        """福田E家登录"""
        print('🔑 福田e家登录')
        data = {
            "password": self.password,
            "version_name": "7.3.23",
            "version_auth": "",
            "device_id": "",
            "device_model": "",
            "ip": "",
            "name": self.phone,
            "version_code": "316",
            "deviceSystemVersion": "11",
            "device_type": "0"
        }
        
        login = self.login_request('/ehomes-new/homeManager/getLoginMember', data)
        
        if not login or login.get('code') != 200:
            print(f"❌ 福田E家登录失败: {login.get('msg') if login else '未知错误'}")
            return False
        
        self.uid = login['data']['uid']
        self.memberComplexCode = login['data']['memberComplexCode']
        self.memberId = login['data']['memberID']
        
        print(f"✅ 登录成功")
        return True

    def simulate_app_open(self):
        """模拟打开APP"""
        #print(f"🔄 模拟登录中")
        data = {
            "memberId": self.memberId,
            "userId": self.uid,
            "userType": "61",
            "uid": self.uid,
            "mobile": self.phone,
            "tel": self.phone,
            "phone": self.phone,
            "brandName": "",
            "seriesName": "",
            "token": "ebf76685e48d4e14a9de6fccc76483e3",
            "safeEnc": self.get_safe_enc_share(),
            "businessId": 1,
            "activityNumber": "open",
            "requestType": "0",
            "type": "5",
            "userNumber": self.memberId,
            "channel": "1",
            "name": "",
            "remark": "打开APP"
        }
        
        result = self.common_request('/ehomes-new/homeManager/api/share/corsToActicity', data)
        
        if result and result.get('code') == 200:
            print(f"✅ 模拟打开APP成功")
            return True
        else:
            print(f"❌ 模拟打开APP失败: {result.get('msg') if result else '未知错误'}")
            return False

    def save_device_info(self):
        """保存友盟设备信息"""
        #print(f"📱 保存友盟设备信息中")
        data = {
            "memberId": self.memberId,
            "userId": self.uid,
            "userType": "61",
            "uid": self.uid,
            "mobile": self.phone,
            "tel": self.phone,
            "phone": self.phone,
            "brandName": "",
            "seriesName": "",
            "token": "ebf76685e48d4e14a9de6fccc76483e3",
            "safeEnc": self.get_safe_enc_share(),
            "businessId": 1,
            "device": "ANDROID",
            "deviceToken": "ApYFnaJD4NEfnlkz_Z9vSmo5YWiYnCm1EvmDDqpYCSvM"
        }
        
        result = self.common_request('/ehomes-new/homeManager/api/message/saveUserDeviceInfo', data)
        
        if result and result.get('code') == 200:
            #print(f"✅ 保存友盟设备信息成功")
            return True
        else:
            error_msg = result.get('msg', '未知错误') if result else '未知错误'
            print(f"❌ 保存友盟设备信息失败: {error_msg}")
            return False

    def futian_sign(self, sign_status):
        """福田E家签到"""
        if sign_status == "未签到":
            print(f"📝 执行福田E家签到")
            
            # 验证必要的登录信息
            if not all([self.memberComplexCode, self.uid, self.phone]):
                print(f"❌ 登录信息不完整，无法签到: memberComplexCode={self.memberComplexCode}, uid={self.uid}, phone={self.phone}")
                return False
            
            data = {
                "memberId": self.memberComplexCode,
                "userId": self.uid,
                "userType": "61",
                "uid": self.uid,
                "mobile": self.phone,
                "tel": self.phone,
                "phone": self.phone,
                "brandName": "",
                "seriesName": "",
                "token": "ebf76685e48d4e14a9de6fccc76483e3",
                "safeEnc": self.get_safe_enc_share(),
                "businessId": 1
            }
            
            try:
                sign = self.common_request('/ehomes-new/homeManager/api/bonus/signActivity2nd', data)
                
                if sign and isinstance(sign, dict) and sign.get('data') and sign['data'].get('integral'):
                    print(f"✅ 签到成功，获得{sign['data']['integral']}积分")
                    return True
                else:
                    error_msg = "未知错误"
                    if sign and isinstance(sign, dict):
                        if 'data' in sign and sign['data']:
                            error_msg = sign['data'].get('msg', '未知错误')
                        else:
                            error_msg = sign.get('msg', '未知错误')
                    print(f"❌ 签到失败: {error_msg}")
                    return False
            except Exception as e:
                print(f"❌ 签到异常: {e}")
                return False
        else:
            print(f"ℹ️ 今日签到状态: {sign_status}")
            return True

    def get_tasks(self):
        """获取每日任务列表"""
        print("————————————————")
        #print("🔍 获取每日任务...")
        
        # 验证必要的登录信息
        if not all([self.memberId, self.uid, self.phone]):
            print(f"❌ 登录信息不完整，无法获取任务: memberId={self.memberId}, uid={self.uid}, phone={self.phone}")
            return []
        
        data = {
            "memberId": self.memberId,
            "userId": self.uid,
            "userType": "61",
            "uid": self.uid,
            "mobile": self.phone,
            "tel": self.phone,
            "phone": self.phone,
            "brandName": "",
            "seriesName": "",
            "token": "ebf76685e48d4e14a9de6fccc76483e3",
            "safeEnc": self.get_safe_enc_share(),
            "businessId": 1
        }
        
        try:
            task_list = self.common_request('/ehomes-new/homeManager/api/Member/getTaskList', data)
            
            if task_list and isinstance(task_list, dict) and 'data' in task_list and isinstance(task_list['data'], list):
                print(f"✅ 获取任务成功，共{len(task_list['data'])}个任务")
                return task_list['data']
            else:
                print(f"❌ 获取任务失败: {task_list.get('msg', '未知错误') if task_list else '请求返回空'}")
                return []
        except Exception as e:
            print(f"❌ 获取任务异常: {e}")
            return []

    def do_share_task(self, rule_id):
        """执行分享任务"""
        print(f"🔄 执行分享任务")
        
        # 获取分享任务专用的safeKey
        share_safe_key_raw = self.get_share_safe_key()
        share_safe_key = str(int(datetime.now().timestamp() * 1000) - share_safe_key_raw)
        
        # 使用新的分享接口
        headers = {
            'Host': 'finance.foton.com.cn',
            'Accept': '*/*',
            'channel': 'H5',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json;charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) ftejIOS',
            'Connection': 'keep-alive'
        }
        
        data = {
            "memberId": self.memberComplexCode,
            "tel": self.phone,
            "id": rule_id,
            "safeEnc": share_safe_key,
            "userId": None
        }
        
        try:
            response = requests.post(
                "https://finance.foton.com.cn/FONTON_PROD/ehomes-new/homeManager//api/bonus/addIntegralForShare",
                headers=headers,
                data=json.dumps(data)
            )
            time.sleep(random.randint(2, 3)) 
            result = response.json()
            
            if result and result.get('code') == 200:
                print(f"✅ 分享成功，获得{result['data'].get('integral', 0)}积分")
                return True
            else:
                print(f"❌ 分享失败: {result.get('msg') if result else '未知错误'}")
                return False
        except Exception as e:
            print(f"❌ 分享请求失败: {e}")
            return False

    def do_follow_task(self):
        """执行关注任务"""
        print(f"👥 执行关注任务")
        # 获取推荐帖子
        data = {
            "memberId": self.memberId,
            "userId": self.uid,
            "userType": "61",
            "uid": self.uid,
            "mobile": self.phone,
            "tel": self.phone,
            "phone": self.phone,
            "brandName": "",
            "seriesName": "",
            "token": "ebf76685e48d4e14a9de6fccc76483e3",
            "safeEnc": self.get_safe_enc_share(),
            "businessId": 1,
            "position": "1",
            "pageNumber": "1",
            "pageSize": 9
        }
        
        posts = self.common_request('/ehomes-new/ehomesCommunity/api/post/recommendPostList', data)
        
        if not posts or 'data' not in posts or not posts['data']:
            print(f"❌ 获取推荐帖子失败")
            return False
        
        # 随机选择一个帖子进行关注
        index = random.randint(0, len(posts['data']) - 1)
        member_id = posts['data'][index]['memberId']
        
        # 关注
        follow_data = {
            "memberId": self.memberComplexCode,
            "userId": self.uid,
            "userType": "61",
            "uid": self.uid,
            "mobile": self.phone,
            "tel": self.phone,
            "phone": self.phone,
            "brandName": "",
            "seriesName": "",
            "token": "ebf76685e48d4e14a9de6fccc76483e3",
            "safeEnc": self.get_safe_enc_share(),
            "businessId": 1,
            "behavior": "1",
            "memberIdeds": member_id,
            "navyId": "null"
        }
        
        follow = self.common_request('/ehomes-new/ehomesCommunity/api/post/follow2nd', follow_data)
        
        if follow and follow.get('code') == 200:
            print(f"✅ 关注成功")
        else:
            print(f"❌ 关注失败: {follow.get('msg') if follow else '未知错误'}")
            
        # 取消关注
        unfollow_data = follow_data.copy()
        unfollow_data["behavior"] = "2"
        
        unfollow = self.common_request('/ehomes-new/ehomesCommunity/api/post/follow2nd', unfollow_data)
        
        if unfollow and unfollow.get('code') == 200:
            print(f"✅ 取关成功")
            return True
        else:
            print(f"❌ 取关失败: {unfollow.get('msg') if unfollow else '未知错误'}")
            return False

    def do_post_task(self):
        """执行发帖任务"""
        print(f"✍️ 执行发帖任务")
        # 获取话题列表
        data = {
            "memberId": self.memberId,
            "userId": self.uid,
            "userType": "61",
            "uid": self.uid,
            "mobile": self.phone,
            "tel": self.phone,
            "phone": self.phone,
            "brandName": "",
            "seriesName": "",
            "token": "ebf76685e48d4e14a9de6fccc76483e3",
            "safeEnc": self.get_safe_enc_share(),
            "businessId": 1
        }
        
        topics = self.login_request('/ehomes-new/ehomesCommunity/api/post/topicList', data)
        
        if not topics or 'data' not in topics or 'top' not in topics['data']:
            print(f"❌ 获取话题列表失败")
            return False
        
        # 随机选择一个话题
        index = random.randint(0, len(topics['data']['top']) - 1)
        topic_id = topics['data']['top'][index]['topicId']
        
        # 获取随机文本
        text = self.text_get()
        if not text or len(text) < 10:
            text = '如果觉得没有朋友，就去找喜欢的人表白，对方会提出和你做朋友的。'
        
        print(f"📝 发帖内容：{text}")
        
        # 发帖
        post_data = {
            "memberId": self.memberComplexCode,
            "userId": self.uid,
            "userType": "61",
            "uid": self.uid,
            "mobile": self.phone,
            "tel": self.phone,
            "phone": self.phone,
            "brandName": "",
            "seriesName": "",
            "token": "ebf76685e48d4e14a9de6fccc76483e3",
            "safeEnc": self.get_safe_enc_share(),
            "businessId": 1,
            "content": text,
            "postType": 1,
            "topicIdList": [topic_id],
            "uploadFlag": 3,
            "title": "",
            "urlList": []
        }
        
        post = self.common_request('/ehomes-new/ehomesCommunity/api/post/addJson2nd', post_data)
        
        if post and isinstance(post, dict) and post.get('code') == 200:
            post_id = None
            if 'data' in post and post['data']:
                post_id = post['data'].get('postId')
            
            if post_id:
                print(f"✅ 发帖成功，帖子ID: {post_id}")
                
                try:
                    # 等待2-3秒确保帖子已保存
                    wait_time = random.randint(2, 3)
                    time.sleep(wait_time)
                    
                    if self.delete_post(post_id):
                        print(f"✅ 帖子删除成功")
                    else:
                        print(f"⚠️ 帖子删除失败，但发帖任务已完成")
                except Exception as e:
                    print(f"⚠️ 删除帖子时异常: {e}")
                
                return post_id  # 返回帖子ID
            else:
                print(f"✅ 发帖成功，但未获取到帖子ID")
                return True
        else:
            print(f"❌ 发帖失败: {post.get('msg') if post else '未知错误'}")
            return False

    def check_points(self):
        """查询积分"""
        print("————————————")
        
        # 验证必要的登录信息
        if not all([self.memberId, self.uid, self.phone]):
            print(f"❌ 登录信息不完整，无法查询积分: memberId={self.memberId}, uid={self.uid}, phone={self.phone}")
            return 0
        
        data = {
            "memberId": self.memberId,
            "userId": self.uid,
            "userType": "61",
            "uid": self.uid,
            "mobile": self.phone,
            "tel": self.phone,
            "phone": self.phone,
            "brandName": "",
            "seriesName": "",
            "token": "ebf76685e48d4e14a9de6fccc76483e3",
            "safeEnc": self.get_safe_enc_share(),
            "businessId": 1
        }
        
        try:
            result = self.common_request('/ehomes-new/homeManager/api/Member/findMemberPointsInfo', data)
            
            if result and isinstance(result, dict) and 'data' in result and result['data']:
                points = result['data'].get('pointValue', 0)
                print(f"🏆 查询当前账号积分: {points}")
                # 使用线程锁保护notice变量的更新
                with self.notice_lock:
                    self.notice += f"用户：{self.phone} 拥有积分: {points}\n"
                return points
            else:
                print(f"❌ 查询积分失败: {result.get('msg', '未知错误') if result else '请求返回空'}")
                return 0
        except Exception as e:
            print(f"❌ 查询积分异常: {e}")
            return 0

    def send_notification(self):
        """发送通知"""
        if not self.notice:
            return
            
        print(f"\n{'='*50}")
        print(f"📊 积分汇总:")
        print(f"{'-'*30}")
        print(self.notice)
        print(f"{'='*50}")
        
        # PushPlus推送
        try:
            pushplus_token = os.environ.get('FT_PUSH_TOKEN', '')
            if pushplus_token:
                self.send_pushplus_notification(pushplus_token, self.notice)
            else:
                print("ℹ️ 未设置FT_PUSH_TOKEN环境变量，跳过推送")
        except Exception as e:
            print(f"⚠️ 推送通知失败: {e}")

    def send_pushplus_notification(self, token, content):
        """发送PushPlus推送通知"""
        try:
            url = "http://www.pushplus.plus/send"
            
            # 构建推送内容
            title = "🏆 福田E家积分汇总"
            
            # 格式化推送内容为HTML
            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">
                        🏆 福田E家积分汇总
                    </h2>
                    <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; font-family: monospace;">
                        {content.replace(chr(10), '<br>')}
                    </div>
                    <p style="text-align: center; color: #7f8c8d; margin-top: 20px; font-size: 12px;">
                        📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    </p>
                </div>
            </div>
            """
            
            data = {
                "token": token,
                "title": title,
                "content": html_content,
                "template": "html"
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('code') == 200:
                print("✅ PushPlus推送发送成功")
            else:
                print(f"❌ PushPlus推送发送失败: {result.get('msg', '未知错误')}")
                
        except Exception as e:
            print(f"❌ PushPlus推送异常: {e}")

    def delete_post(self, post_id):
        """删除指定帖子"""
        
        # 验证必要的登录信息
        if not all([self.memberComplexCode, self.uid, self.phone]):
            print(f"❌ 登录信息不完整，无法删除帖子: memberComplexCode={self.memberComplexCode}, uid={self.uid}, phone={self.phone}")
            return False
        
        data = {
            "memberId": self.memberId,
            "userId": self.uid,
            "userType": "61",
            "uid": self.uid,
            "mobile": self.phone,
            "tel": self.phone,
            "phone": self.phone,
            "brandName": "",
            "seriesName": "",
            "token": "ebf76685e48d4e14a9de6fccc76483e3",
            "safeEnc": self.get_safe_enc_share(),
            "businessId": 1,
            "postId": post_id
        }
        
        try:
            result = self.common_request('/ehomes-new/ehomesCommunity/api/mine/delete', data)
            
            if result and isinstance(result, dict) and result.get('code') == 200:
                return True
            else:
                print(f"❌ 帖子删除失败: {result.get('msg', '未知错误') if result else '请求返回空'}")
                return False
        except Exception as e:
            print(f"❌ 删除帖子异常: {e}")
            return False

    def run_account(self):
        """运行单个账号的所有任务"""
        try:
            # 清空本次运行的帖子记录
            self.current_session_posts.clear()
            
            # 验证账号信息
            if not self.phone or not self.password:
                print(f"❌ 账号信息不完整: 手机号={self.phone}, 密码={'已设置' if self.password else '未设置'}")
                return False

            # 获取皮卡生活safeKey
            if not self.get_pika_safe_key():
                print("⚠️ 获取皮卡生活safeKey失败，但继续执行")
            
            # 皮卡生活登录和签到
            if not self.pika_login():
                print(f"❌ 皮卡生活登录失败，跳过该账号")
                return False

            # 执行皮卡生活签到
            try:
                self.pika_sign()
            except Exception as e:
                print(f"⚠️ 皮卡生活签到异常: {e}")

            # 获取福田E家safeKey
            if not self.get_futian_safe_key():
                print("⚠️ 获取福田E家safeKey失败，但继续执行")

            # 福田E家登录和相关任务
            if not self.futian_login():
                print(f"❌ 福田E家登录失败，跳过该账号")
                return False
            
            # 验证登录后的必要信息
            if not all([self.uid, self.memberComplexCode, self.memberId]):
                print(f"❌ 登录后信息不完整: uid={self.uid}, memberComplexCode={self.memberComplexCode}, memberId={self.memberId}")
                return False
                
            # 模拟打开APP
            try:
                self.simulate_app_open()
            except Exception as e:
                print(f"⚠️ 模拟打开APP异常: {e}")
            
            # 保存设备信息
            try:
                self.save_device_info()
            except Exception as e:
                print(f"⚠️ 保存设备信息异常: {e}")
            
            # 签到
            try:
                login_result = self.login_request('/ehomes-new/homeManager/getLoginMember', {
                    "password": self.password,
                    "name": self.phone,
                    "version_code": "316",
                    "device_type": "0"
                })
                
                sign_status = "未签到"
                if login_result and isinstance(login_result, dict) and 'data' in login_result and login_result['data']:
                    sign_status = login_result['data'].get('signIn', '未签到')
                
                self.futian_sign(sign_status)
            except Exception as e:
                print(f"⚠️ 福田E家签到异常: {e}")
            
            # 执行每日任务
            try:
                tasks = self.get_tasks()
                
                if not tasks:
                    print("⚠️ 未获取到任务列表")
                else:
                    for task in tasks:
                        try:
                            task_name = task.get('ruleName', '未知任务')
                            task_id = task.get('ruleId', '')
                            is_complete = task.get('isComplete', '0')
                            
                            print(f"📌 任务：{task_name}")
                            
                            if is_complete == "1":
                                print('✅ 任务已完成')
                                continue
                                
                            # 分享任务
                            if task_id == "33":
                                try:
                                    self.do_share_task(task_id)
                                except Exception as e:
                                    print(f"⚠️ 分享任务执行异常: {e}")
                            
                            # 关注任务
                            elif task_id == "130":
                                try:
                                    self.do_follow_task()
                                except Exception as e:
                                    print(f"⚠️ 关注任务执行异常: {e}")
                                    
                            # 发帖任务
                            elif task_id == "125":
                                if self.enable_post_task:
                                    try:
                                        post_result = self.do_post_task()
                                        if post_result:
                                            print(f"✅ 发帖任务完成")
                                    except Exception as e:
                                        print(f"⚠️ 发帖任务执行异常: {e}")
                                else:
                                    print(f"ℹ️ 发帖任务已禁用（FT_FT=False）")
                            
                            # 任务间随机等待
                            time.sleep(random.randint(1, 3))
                            
                        except Exception as e:
                            print(f"⚠️ 处理任务异常: {e}")
                            continue
                            
            except Exception as e:
                print(f"⚠️ 获取或执行任务异常: {e}")
            
            # 查询积分
            try:
                self.check_points()
            except Exception as e:
                print(f"⚠️ 查询积分异常: {e}")
            
            print(f"✅ 账号 {self.phone} 所有任务执行完成")
            return True
            
        except Exception as e:
            print(f"❌ 账号 {self.phone} 运行出错: {str(e)}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return False

    def run(self):
        """运行所有账号"""
        
        # 显示公告信息
        print("="*60)
        print("🎉 呆呆粉丝后援会：996374999")
        print("="*60)
        
        if not self.accounts:
            print(f"❌ 请先设置环境变量Fukuda，格式为空格分隔的'账号#密码'列表")
            return
        
        # 过滤空账号
        valid_accounts = [acc for acc in self.accounts if acc.strip()]
        if not valid_accounts:
            print(f"❌ 没有有效的账号信息")
            return
            
        # 随机打乱账号顺序
        random.shuffle(valid_accounts)
        print(f"ℹ️ 共{len(valid_accounts)}个账号，并发数: {self.concurrent_workers}")
        print(f"ℹ️ 发帖任务: {'启用' if self.enable_post_task else '禁用'}")
        
        if self.concurrent_workers <= 1:
            # 串行执行
            print(f"🔄 串行执行模式")
            for i, account in enumerate(valid_accounts):
                try:
                    self.phone = account.split("#")[0]
                    self.password = account.split("#")[1]
                    
                    print(f"{'='*50}")
                    print(f"👤 账号 {i+1}/{len(valid_accounts)}: {self.phone}")
                    
                    self.run_account()
                    
                    # 在账号之间随机等待3-8秒
                    if i < len(valid_accounts) - 1:
                        wait_time = random.randint(3, 8)
                        print(f"\n⏳ 等待{wait_time}秒后运行下一个账号...")
                        time.sleep(wait_time)
                except Exception as e:
                    print(f"❌ 账号信息解析错误: {str(e)}")
        else:
            # 并发执行
            print(f"🚀 并发执行模式，最大并发数: {self.concurrent_workers}")
            
            with ThreadPoolExecutor(max_workers=self.concurrent_workers) as executor:
                # 提交所有任务
                future_to_account = {
                    executor.submit(self.run_single_account, account, i, len(valid_accounts)): account 
                    for i, account in enumerate(valid_accounts)
                }
                
                # 等待任务完成并收集结果
                completed_count = 0
                for future in as_completed(future_to_account):
                    account = future_to_account[future]
                    completed_count += 1
                    try:
                        result = future.result()
                        print(f"[{completed_count}/{len(valid_accounts)}] {result}")
                    except Exception as e:
                        phone = account.split("#")[0] if "#" in account else "未知"
                        print(f"[{completed_count}/{len(valid_accounts)}] ❌ 账号 {phone} 执行异常: {str(e)}")
                
                print(f"\n🎉 所有账号处理完成！")
                
        # 发送通知
        self.send_notification()

    def run_single_account(self, account_info, account_index, total_accounts):
        """运行单个账号的所有任务（用于并发执行）"""
        try:
            phone = account_info.split("#")[0]
            password = account_info.split("#")[1]
            
            print(f"{'='*50}")
            print(f"👤 账号 {account_index+1}/{total_accounts}: {phone}")
            
            # 创建账号专用的实例数据
            account_data = {
                'phone': phone,
                'password': password,
                'memberNo': "",
                'token': "",
                'uid': "",
                'memberComplexCode': "",
                'memberId': "",
                'base_url': "https://czyl.foton.com.cn",
                'signed': False,
                'pika_safe_key': None,
                'futian_safe_key': None,
                'current_session_posts': [],
                'enable_post_task': self.enable_post_task
            }
            
            # 临时设置当前账号信息
            original_phone = self.phone
            original_password = self.password
            original_memberNo = self.memberNo
            original_token = self.token
            original_uid = self.uid
            original_memberComplexCode = self.memberComplexCode
            original_memberId = self.memberId
            original_signed = self.signed
            original_pika_safe_key = self.pika_safe_key
            original_futian_safe_key = self.futian_safe_key
            original_current_session_posts = self.current_session_posts.copy()
            original_enable_post_task = self.enable_post_task
            
            try:
                # 设置当前账号信息
                self.phone = account_data['phone']
                self.password = account_data['password']
                self.memberNo = account_data['memberNo']
                self.token = account_data['token']
                self.uid = account_data['uid']
                self.memberComplexCode = account_data['memberComplexCode']
                self.memberId = account_data['memberId']
                self.signed = account_data['signed']
                self.pika_safe_key = account_data['pika_safe_key']
                self.futian_safe_key = account_data['futian_safe_key']
                self.current_session_posts = account_data['current_session_posts']
                self.enable_post_task = account_data['enable_post_task']
                
                # 执行账号任务
                self.run_account()
                
                return f"✅ 账号 {phone} 执行完成"
                
            finally:
                # 恢复原始数据
                self.phone = original_phone
                self.password = original_password
                self.memberNo = original_memberNo
                self.token = original_token
                self.uid = original_uid
                self.memberComplexCode = original_memberComplexCode
                self.memberId = original_memberId
                self.signed = original_signed
                self.pika_safe_key = original_pika_safe_key
                self.futian_safe_key = original_futian_safe_key
                self.current_session_posts = original_current_session_posts
                self.enable_post_task = original_enable_post_task
                
        except Exception as e:
            return f"❌ 账号 {phone if 'phone' in locals() else '未知'} 运行出错: {str(e)}"

def main():
    """主函数入口"""
    ftej = FutianEJia()
    ftej.run()

if __name__ == "__main__":
    wait_sec = random.randint(10, 50)
    print(f"等待{wait_sec}秒后继续上传听书时长...", "info")
    time.sleep(wait_sec)
    main()