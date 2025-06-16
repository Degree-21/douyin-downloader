import base64
import json
from typing import Optional, List, Dict, Union
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models


class TencentASRClient:
    """
    腾讯云语音识别(ASR)客户端

    封装了录音文件识别相关接口，简化调用过程

    文档参考：https://cloud.tencent.com/document/product/1093/37823
    """

    def __init__(self, secret_id: str, secret_key: str, region: str = "ap-shanghai"):
        """
        初始化客户端

        :param secret_id: 腾讯云API密钥ID
        :param secret_key: 腾讯云API密钥Key
        :param region: 地域，默认为上海
        """
        cred = credential.Credential(secret_id, secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = "asr.tencentcloudapi.com"

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        self.client = asr_client.AsrClient(cred, region, client_profile)

    def create_rec_task(
            self,
            engine_model_type: str,
            channel_num: int,
            res_text_format: int,
            source_type: int,
            url: Optional[str] = None,
            data: Optional[Union[str, bytes]] = None,
            data_len: Optional[int] = None,
            callback_url: Optional[str] = None,
            speaker_diarization: Optional[int] = None,
            speaker_number: Optional[int] = None,
            hotword_id: Optional[str] = None,
            customization_id: Optional[str] = None,
            emotion_recognition: Optional[int] = None,
            emotional_energy: Optional[int] = None,
            convert_num_mode: Optional[int] = None,
            filter_dirty: Optional[int] = None,
            filter_punc: Optional[int] = None,
            filter_modal: Optional[int] = None,
            sentence_max_length: Optional[int] = None,
            extra: Optional[str] = None,
            hotword_list: Optional[str] = None,
            keyword_lib_id_list: Optional[List[str]] = None,
            replace_text_id: Optional[str] = None
    ) -> Dict:
        """
        创建录音文件识别任务

        :param engine_model_type: 引擎模型类型
        :param channel_num: 识别声道数
        :param res_text_format: 识别结果返回样式
        :param source_type: 音频数据来源(0:音频URL;1:音频数据)
        :param url: 音频URL的地址(SourceType为0时必填)
        :param data: 音频数据(SourceType为1时必填)
        :param data_len: 数据长度(未base64编码时的长度)
        :param callback_url: 回调URL
        :param speaker_diarization: 是否开启说话人分离
        :param speaker_number: 说话人分离人数
        :param hotword_id: 热词表id
        :param customization_id: 自学习定制模型id
        :param emotion_recognition: 情绪识别能力
        :param emotional_energy: 情绪能量值
        :param convert_num_mode: 阿拉伯数字智能转换
        :param filter_dirty: 脏词过滤
        :param filter_punc: 标点符号过滤
        :param filter_modal: 语气词过滤
        :param sentence_max_length: 单标点最多字数
        :param extra: 附加参数
        :param hotword_list: 临时热词表
        :param keyword_lib_id_list: 关键词识别ID列表
        :param replace_text_id: 替换词汇表id
        :return: 包含TaskId的字典
        """
        req = models.CreateRecTaskRequest()

        # 必填参数
        req.EngineModelType = engine_model_type
        req.ChannelNum = channel_num
        req.ResTextFormat = res_text_format
        req.SourceType = source_type

        # 根据SourceType设置不同参数
        if source_type == 0:
            if not url:
                raise ValueError("url is required when SourceType is 0")
            req.Url = url
        elif source_type == 1:
            if not data:
                raise ValueError("data is required when SourceType is 1")

            if isinstance(data, bytes):
                data = base64.b64encode(data).decode('utf-8')
            req.Data = data

            if data_len:
                req.DataLen = data_len
            else:
                # 如果没有提供data_len，则尝试从data计算
                try:
                    decoded_data = base64.b64decode(data)
                    req.DataLen = len(decoded_data)
                except:
                    pass

        # 可选参数
        if callback_url is not None:
            req.CallbackUrl = callback_url
        if speaker_diarization is not None:
            req.SpeakerDiarization = speaker_diarization
        if speaker_number is not None:
            req.SpeakerNumber = speaker_number
        if hotword_id is not None:
            req.HotwordId = hotword_id
        if customization_id is not None:
            req.CustomizationId = customization_id
        if emotion_recognition is not None:
            req.EmotionRecognition = emotion_recognition
        if emotional_energy is not None:
            req.EmotionalEnergy = emotional_energy
        if convert_num_mode is not None:
            req.ConvertNumMode = convert_num_mode
        if filter_dirty is not None:
            req.FilterDirty = filter_dirty
        if filter_punc is not None:
            req.FilterPunc = filter_punc
        if filter_modal is not None:
            req.FilterModal = filter_modal
        if sentence_max_length is not None:
            req.SentenceMaxLength = sentence_max_length
        if extra is not None:
            req.Extra = extra
        if hotword_list is not None:
            req.HotwordList = hotword_list
        if keyword_lib_id_list is not None:
            req.KeyWordLibIdList = keyword_lib_id_list
        if replace_text_id is not None:
            req.ReplaceTextId = replace_text_id

        try:
            resp = self.client.CreateRecTask(req)
            return {
                "TaskId": resp.Data.TaskId,
                "RequestId": resp.RequestId
            }
        except TencentCloudSDKException as e:
            raise Exception(f"Tencent Cloud SDK Exception: {e}")

    def create_rec_task_by_url(
            self,
            url: str,
            engine_model_type: str = "16k_zh",
            channel_num: int = 1,
            res_text_format: int = 0,
            **kwargs
    ) -> Dict:
        """
        通过音频URL创建识别任务(简化版)

        :param url: 音频URL地址
        :param engine_model_type: 引擎模型类型，默认16k_zh
        :param channel_num: 识别声道数，默认1
        :param res_text_format: 识别结果返回样式，默认0
        :param kwargs: 其他可选参数
        :return: 包含TaskId的字典
        """
        return self.create_rec_task(
            engine_model_type=engine_model_type,
            channel_num=channel_num,
            res_text_format=res_text_format,
            source_type=0,
            url=url,
            **kwargs
        )

    def create_rec_task_by_data(
            self,
            data: Union[str, bytes],
            engine_model_type: str = "16k_zh",
            channel_num: int = 1,
            res_text_format: int = 0,
            **kwargs
    ) -> Dict:
        """
        通过音频数据创建识别任务(简化版)

        :param data: 音频数据(base64编码字符串或bytes)
        :param engine_model_type: 引擎模型类型，默认16k_zh
        :param channel_num: 识别声道数，默认1
        :param res_text_format: 识别结果返回样式，默认0
        :param kwargs: 其他可选参数
        :return: 包含TaskId的字典
        """
        return self.create_rec_task(
            engine_model_type=engine_model_type,
            channel_num=channel_num,
            res_text_format=res_text_format,
            source_type=1,
            data=data,
            **kwargs
        )

    def describe_task_status(self, task_id: int) -> Dict:
        """
        查询录音文件识别结果

        :param task_id: 任务ID
        :return: 任务状态信息
        """
        req = models.DescribeTaskStatusRequest()
        req.TaskId = task_id

        try:
            resp = self.client.DescribeTaskStatus(req)
            return {
                "TaskId": resp.Data.TaskId,
                "Status": resp.Data.Status,
                "StatusStr": resp.Data.StatusStr,
                "Result": resp.Data.Result,
                "ErrorMsg": resp.Data.ErrorMsg,
                "ResultDetail": resp.Data.ResultDetail,
                "RequestId": resp.RequestId
            }
        except TencentCloudSDKException as e:
            raise Exception(f"Tencent Cloud SDK Exception: {e}")