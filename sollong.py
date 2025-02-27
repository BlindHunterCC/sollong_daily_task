"""
  @ Author:   Mr.Hat
  @ Date:     2024/3/5 14:26
  @ Description: 
  @ History:
"""
from curl_cffi.requests import AsyncSession
import asyncio
import os
import time
import random
from logger import logger
from faker import Faker
from solathon import Keypair
import requests


async def create_account(amount, invite_code='',file_name=None, save=True):
    """ 创建Solana钱包账户
    :param amount: 需要创建的钱包账户数量
    :param file_name: 需要存储的txt文件名称，名称包含".txt"
    :param save: 是否存储为文件类型，True为存储，False为不存储文件类型，这里是为了方便下方自动生成账户，自动邀请逻辑自行处理
    :return:
    """
    accounts = []
    for i in range(amount):
        new_account = Keypair()
        accounts.append(new_account)

    if save:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_directory, "wallets", "daily_task", file_name)
        with open(file_path, 'w', encoding='utf-8') as file:
            for wallet_data in accounts:
                file.write(f"{wallet_data.public_key},{wallet_data.private_key}\n")

            file.close()

        file_path = os.path.join(current_directory, "wallets", "daily_task", "autoSign.txt")
        with open(file_path, 'a', encoding='utf-8') as file:
            for wallet_data in accounts:
                file.write(f"{wallet_data.public_key},{wallet_data.private_key}\n")
        
            file.close()

        logger.success(f"生成钱包成功, 数量为: {amount},  该钱包使用邀请码： {invite_code}")
    else:
        return accounts


class Sollong(object):
    def __init__(self, private_key, invite_code, proxies=None):
        self.fake = Faker()
        self._key_pair = Keypair().from_private_key(private_key)
        self._invite_code = invite_code
        headers = {
            "Referer": "https://app.sollong.xyz/",
            "Origin": "https://app.sollong.xyz",
            "User-Agent": self.fake.chrome()
        }
        self._http = AsyncSession(timeout=120, headers=headers, impersonate="chrome120", proxies=proxies)

    async def superiors(self):
        """ 检测钱包是否已经注册
        :return:
        """
        uri = f"https://api.v-token.io/api/points/superiors?address={self._key_pair.public_key}"
        try:
            res = await self._http.get(uri)
            if res.status_code == 200 and "code" in res.text:
                if res.json()["code"] == 200:
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"检测 Superiors失败 {e}")
            return False

    async def home(self):
        """ 查询当前钱包详细情况
        :return:
        """
        uri = f"https://api.v-token.io/api/points/home?address={self._key_pair.public_key}"
        try:
            res = await self._http.get(uri)
            if res.status_code == 200 and "code" in res.text:
                if res.json()["code"] == 200:
                    return res.json()["data"]
                else:
                    return False
        except Exception as e:
            logger.error(f"检测Home失败 {e}")
            return False

    async def invite(self):
        """ 邀请新账户。
        :return:
        """
        uri = "https://api.v-token.io/api/points/invite"
        json_data = {
            "invite_code": self._invite_code,
            "address": str(self._key_pair.public_key)
        }
        try:
            res = await self._http.post(uri, json=json_data)
            if res.status_code == 200 and "code" in res.text and res.json()["code"] == 200:
                return True
            return False
        except Exception as e:
            logger.error(f"邀请失败 {e}")
            return False

    async def sign(self):
        """ 钱包每日签名
        :return:
        """
        uri = "https://api.v-token.io/api/points/sign"

        timestamp = int(time.time())
        message = f"sign in{timestamp}"
        sign_res = self._key_pair.sign(message=message)
        sign_ = sign_res.hex()[:128]  # 实际签名长度大于需要的签名字段长度，截取所需部分

        json_data = {
            "sign": sign_,
            "address": str(self._key_pair.public_key),
            "timestamp": timestamp
        }
        try:
            res = await self._http.post(uri, json=json_data)

            if res.status_code == 200:
                if "code" in res.text:
                    if res.json()["code"] == 400:
                        return False
                    if res.json()["code"] == 200:
                        return True

                return None
        except Exception as e:
            logger.error(f"签名失败 {e}")
            return None

    async def daily_task(self):
        """ 每日任务
        :return:
        """
        if await self.home() is False and await self.superiors() is False:  # 确认账户没有注册，并且进行注册
            # 没有注册，进行邀请注册
            if await self.invite():
                if await self.sign():
                    logger.info(f"地址：{self._key_pair.public_key}被 {self._invite_code}邀请注册并签到完成！")
                    return True
        else:
            if await self.sign():
                logger.info(f"地址：{self._key_pair.public_key}签到完成！")
                return True


async def operate(invite_code, file_name):
    """ 通过自动生成的钱包地址来进行邀请，需要配置代理信息
    :param invite_code: 邀请码
    :param file_name: 需要执行的txt文件路径
    :return:
    """
    current_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_directory, "wallets", "daily_task", file_name)

    with open(file_path, "r") as file:
        for i in file:
            source = i.strip().split(",")
            prox = r'用户名:密码@IP:端口'
            address = source[0]
            private = source[1]

            proxies = {
                "http": f"http://{prox}",
                "https": f"http://{prox}"
            }
            # session = requests.Session()
            # proxies = {'http': f'socks5://{prox}',
            #            'https': f'socks5://{prox}'}
            # session.proxies = proxies

            sl = Sollong(private_key=private, invite_code=invite_code, proxies=proxies)
            await sl.daily_task()

def getInviteCode(file_name):
    """ 取得邀请码
    :param file_name: 需要执行的txt文件路径
    :return:
    """
    current_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_directory, "wallets", "daily_task", file_name)

    inviteCodes = []
    with open(file_path, "r") as file:
        for line in file:
            inviteCodes.append(line.replace('\n',''))

    return inviteCodes

async def test():
    asyncio.sleep(3)
    logger.info('test run')

async def inviteAcount(random_Count,invite_code,file_name):
    """ 邀请新账户
    :param random_Count：创建新账户个数
    :param invite_code：使用的邀请码
    :param file_name: 需要执行的txt文件路径
    :return:
    """
    await create_account(random_Count, invite_code,file_name)
    await operate(invite_code,file_name)
    #await test()

if __name__ == '__main__':
    
    opt = input("如果想签到请选择1，\n如果想邀请新用户请选择2：\n")
    if opt == '1':
        asyncio.run(operate("2t6g6d", "signAcount.txt"))
    elif opt == '2':
        count = 0
        while(1):
            try:
                count = int(input("请输入想要邀请用户个数：\n"))
                break
            except Exception:
                logger.error("输入了不是数字的字符，请重新输入！\n")
        
        """
        从文件中取到所有的邀请码，随机选中邀请码 创建新用户钱包并邀请
        """
        inviteCodes = getInviteCode('inviteCode.txt')
        while(count > 0):
            inviteCode = random.choice(inviteCodes)
            randomCount = random.randint(1,30)

            if (count <= randomCount):
                randomCount = count
                count = 0
            else:
                count = count - randomCount

            asyncio.run(inviteAcount(randomCount,inviteCode,"test.txt"))


    else:
        logger.error("选择类型错误！")
    
    """
        以下是生成钱包账户的测试例子。
        Note：每日生成钱包都会自动覆盖之前生成的内容，需要自行保存处理，方便后期使用。
        
    """
    #asyncio.run(create_account(10, "test.txt"))
    """
        以下是使用邀请码，自动邀请测试用例
    """
    #asyncio.run(operate("2t6g6d", "test.txt"))
