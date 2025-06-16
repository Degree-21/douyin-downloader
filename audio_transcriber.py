import os
import base64
import time
from datetime import datetime, timedelta

import yaml
from pydub import AudioSegment
from tencentcloud.common import credential
from tencentcloud.asr.v20190614 import asr_client, models
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile


class TencentASRClient:
    """腾讯云语音识别客户端封装（根据最新API文档修正）"""

    def __init__(self, secret_id, secret_key, region="ap-shanghai"):
        cred = credential.Credential(str(secret_id), str(secret_key))

        # 增强HTTP配置
        http_profile = HttpProfile()
        http_profile.endpoint = "asr.tencentcloudapi.com"
        http_profile.reqTimeout = 60  # 请求超时时间(秒)
        http_profile.keepAlive = True  # 保持连接

        # 增强客户端配置
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        client_profile.unsignedPayload = False  # 启用签名

        # 配置重试策略
        client_profile.disable_retry = False  # 启用自动重试
        client_profile.max_retry_num = 3  # 最大重试次数
        client_profile.retry_delay = 5  # 重试间隔(秒)

        self.client = asr_client.AsrClient(cred, region, client_profile)

    def transcribe_audio(self, audio_path, engine_model_type="16k_zh", res_text_format=0, callback_url=None):
        """使用腾讯云ASR识别音频文件（修正请求参数）"""
        try:
            # 检查文件大小（不超过5MB）
            file_size = os.path.getsize(audio_path)
            if file_size > 5 * 1024 * 1024:  # 5MB限制
                raise ValueError("本地音频文件不能大于5MB")

            # 读取音频文件并转换为base64
            with open(audio_path, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode('utf-8')

            # 创建请求对象
            req = models.CreateRecTaskRequest()

            # 设置必填参数（按照API文档要求）
            req.EngineModelType = engine_model_type
            req.ChannelNum = 1  # 单声道
            req.ResTextFormat = res_text_format  # 结果格式
            req.SourceType = 1  # 1表示本地音频文件

            # 设置音频数据参数
            req.Data = audio_data
            req.DataLen = file_size

            # 设置可选参数
            if callback_url:
                req.CallbackUrl = callback_url

            # 发送请求（SDK会自动处理Action和Version）
            resp = self.client.CreateRecTask(req)

            # 检查响应
            if not resp or not resp.Data or not resp.Data.TaskId:
                raise Exception("腾讯云ASR未返回有效的TaskId")

            return {
                "TaskId": resp.Data.TaskId,
                "RequestId": resp.RequestId
            }

        except TencentCloudSDKException as e:
            raise Exception(f"腾讯云ASR调用失败: {e.message}") from e
        except Exception as e:
            raise Exception(f"音频处理失败: {str(e)}") from e

    def get_transcription_result(self, task_id):
        """获取识别结果"""
        req = models.DescribeTaskStatusRequest()
        req.TaskId = task_id
        req._deserialize({"Action": "DescribeTaskStatus", "Version": self.version})

        try:
            resp = self.client.DescribeTaskStatus(req)
            if not resp.Data:
                raise Exception("未获取到有效的响应数据")

            return {
                "Status": resp.Data.Status,
                "Result": str(resp.Data.Result) if resp.Data.Result else "",
                "ErrorMsg": str(resp.Data.ErrorMsg) if resp.Data.ErrorMsg else "",
                "RequestId": resp.RequestId
            }
        except TencentCloudSDKException as e:
            raise Exception(f"获取识别结果失败: {e.message}") from e

    def get_task_status(self, task_id):
        """获取完整任务状态（修正版）"""
        try:
            # 创建请求对象
            req = models.DescribeTaskStatusRequest()
            req.TaskId = task_id  # 只需要设置TaskId即可

            # 发送请求（SDK会自动处理Action和Version）
            resp = self.client.DescribeTaskStatus(req)

            if not resp or not resp.Data:
                raise Exception("未获取到有效的响应数据")

            # 返回格式化后的结果
            return {
                "TaskId": str(resp.Data.TaskId) if resp.Data.TaskId else "",
                "Status": resp.Data.Status,
                "StatusStr": str(resp.Data.StatusStr) if resp.Data.StatusStr else "",
                "Result": str(resp.Data.Result) if resp.Data.Result else "",
                "ErrorMsg": str(resp.Data.ErrorMsg) if resp.Data.ErrorMsg else "",
                "ResultDetail": str(resp.Data.ResultDetail) if resp.Data.ResultDetail else "",
                "RequestId": resp.RequestId
            }

        except TencentCloudSDKException as e:
            raise Exception(f"获取任务状态失败: {e.message}") from e


# 以下是原有辅助函数，保持不变
def load_config(config_path):
    """加载 YAML 配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            if not config:
                raise ValueError("配置文件为空或格式不正确")

            # 确保关键字段是字符串类型
            if 'tencent_secret_id' in config:
                config['tencent_secret_id'] = str(config['tencent_secret_id'])
            if 'tencent_secret_key' in config:
                config['tencent_secret_key'] = str(config['tencent_secret_key'])

            return config
    except Exception as e:
        raise Exception(f"加载配置文件失败: {str(e)}") from e


def save_transcription_to_file(mp3_path, text):
    """将识别结果保存到与MP3同目录的文本文件中"""
    try:
        base_path = os.path.splitext(mp3_path)[0]
        output_path = f"{base_path}.txt"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(text))

        return output_path
    except Exception as e:
        raise Exception(f"保存识别结果失败: {str(e)}") from e


def process_mp3_files(directory, asr_client):
    """遍历目录并处理所有 MP3 文件（增加结果文件存在检查）"""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp3'):
                mp3_path = os.path.join(root, file)
                txt_path = os.path.splitext(mp3_path)[0] + ".txt"

                # 检查结果文件是否已存在
                if os.path.exists(txt_path):
                    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 跳过已处理文件: {mp3_path}")
                    continue

                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在处理: {mp3_path}")

                try:
                    # 提交识别任务
                    response = asr_client.transcribe_audio(mp3_path)
                    task_id = response["TaskId"]
                    print(f"任务已提交，Task ID: {task_id}, Request ID: {response['RequestId']}")

                    # 轮询获取结果（最多等待10分钟）
                    max_wait_time = timedelta(minutes=10)
                    start_time = datetime.now()
                    result = None
                    poll_interval = 2  # 初始轮询间隔2秒

                    while datetime.now() - start_time < max_wait_time:
                        status = asr_client.get_task_status(task_id)

                        if status['Status'] == 2:  # 成功
                            result = status['Result']
                            print("识别成功！")
                            break
                        elif status['Status'] == 3:  # 失败
                            raise Exception(f"识别失败: {status.get('ErrorMsg', '未知错误')}")

                        # 动态调整轮询间隔
                        print(f"任务处理中... ({status['StatusStr']})")
                        time.sleep(poll_interval)
                        poll_interval = min(poll_interval * 1.5, 10)

                    if result:
                        output_path = save_transcription_to_file(mp3_path, result)
                        print(f"识别结果已保存到: {output_path}")
                    else:
                        print("识别超时，结果未返回")
                        error_path = os.path.splitext(mp3_path)[0] + "_timeout.txt"
                        with open(error_path, 'w', encoding='utf-8') as f:
                            f.write("识别超时，结果未返回")

                except Exception as e:
                    print(f"处理文件 {mp3_path} 时出错: {str(e)}")
                    error_path = os.path.splitext(mp3_path)[0] + "_error.txt"
                    with open(error_path, 'w', encoding='utf-8') as f:
                        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{str(e)}")


def validate_config(config):
    """验证配置文件内容"""
    required_fields = ['path', 'tencent_secret_id', 'tencent_secret_key']
    missing_fields = [field for field in required_fields if field not in config or not config[field]]

    if missing_fields:
        raise ValueError(f"配置文件中缺少必要字段: {', '.join(missing_fields)}")

    if not os.path.exists(config['path']):
        raise ValueError(f"指定路径不存在: {config['path']}")


def main():
    config_file = 'config.yml'

    try:
        config = load_config(config_file)
        validate_config(config)

        target_path = config['path']
        secret_id = config['tencent_secret_id']
        secret_key = config['tencent_secret_key']

        asr_client = TencentASRClient(secret_id, secret_key)

        print(f"开始处理路径: {target_path}")
        process_mp3_files(target_path, asr_client)
        print("所有 MP3 文件处理完成")

    except FileNotFoundError:
        print(f"错误: 配置文件 {config_file} 未找到")
    except yaml.YAMLError as e:
        print(f"YAML 解析错误: {str(e)}")
    except ValueError as e:
        print(f"配置错误: {str(e)}")
    except Exception as e:
        print(f"发生错误: {str(e)}")


if __name__ == "__main__":
    main()