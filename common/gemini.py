# common/gemini.py
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from io import BytesIO
from PIL import Image


from common.logger import timefn
from common.logger import init_logger

class Gemini:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        self.client = genai.Client(api_key=self.api_key)
        self.model = 'gemini-2.0-flash'
        self.model_image = 'gemini-2.5-flash-image' # gemini-2.5-flash-image | gemini-3-pro-image-preview
        self.max_retries = 3
        self.initial_delay = 1


    def retry_with_delay(func):
        def wrapper(self, *args, **kwargs):
            delay = self.initial_delay
            for attempt in range(self.max_retries):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise e
                    # logger.error(f"gemini 호출 {attempt + 1}번째 실패: {e}")
                    time.sleep(delay)
                    delay *= 2

        return wrapper


    @retry_with_delay
    @timefn
    def generate_gemini_content(self, prompt, system_prompt=None, reference=None):

        content_parts = [prompt]

        if reference:
            for ref_path in reference:
                try:
                    if os.path.exists(ref_path):
                        image = Image.open(ref_path)
                        content_parts.append(image)
                        print(f"  -> 레퍼런스 이미지 로드: {os.path.basename(ref_path)}")
                    else:
                        print(f"경고: 레퍼런스 파일을 찾을 수 없습니다. ({ref_path})")
                except Exception as e:
                    print(f"경고: 이미지 로드 중 에러 발생 ({ref_path}): {e}")


        response = self.client.models.generate_content(
            model=self.model,
            contents=content_parts,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt
            ) if system_prompt else None
        )

        return response.text


    @retry_with_delay
    @timefn
    def generate_gemini_image(self, prompt, system_prompt=None, reference=None):
        """
        prompt (str): 생성 프롬프트
        reference (list): 이미지 경로 리스트 ['.png', '.png']
        system_prompt (str): 시스템 프롬프트 (옵션)
        """

        # parts 리스트 생성 (프롬프트 포함)
        parts = [prompt]

        if reference:
            for ref_path in reference:
                try:
                    if os.path.exists(ref_path):
                        image = Image.open(ref_path)
                        # [수정] google.genai 클라이언트는 PIL.Image 객체를 직접 처리할 수 있습니다.
                        # 복잡한 types.Part 변환 없이 바로 리스트에 추가합니다.
                        parts.append(image)
                        print(f" -> 레퍼런스 이미지 로드: {os.path.basename(ref_path)}")
                    else:
                        print(f"경고: 레퍼런스 파일을 찾을 수 없습니다. ({ref_path})")
                except Exception as e:
                    print(f"경고: 이미지 로드 중 에러 발생 ({ref_path}): {e}")

        response = self.client.models.generate_content(
            model=self.model_image,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                image_config=types.ImageConfig(
                    aspect_ratio="3:4",  # 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
                    # image_size="4K" # 1K | 2K | 4K
                ),
                response_modalities=["IMAGE"],
            ),
            contents=parts,
        )


        if response.candidates:
            for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:

                        # 텍스트 응답이 있는 경우 (거절 메시지 등)
                        if part.text:
                            print(f"Text Response: {part.text}")

                        # 이미지 데이터(Inline Data)가 있는 경우
                        if part.inline_data:
                            print("이미지 데이터 수신됨. 변환 중...")

                            # Base64 데이터를 디코딩하여 이미지로 변환
                            image_data = part.inline_data.data
                            image = Image.open(BytesIO(image_data))
                            # image.verify() # verify 후에는 다시 open해야 할 수 있어 주석 처리
                            print("이미지 변환 성공")
                            return image

        print("생성된 이미지가 응답에 없습니다.")
        return None