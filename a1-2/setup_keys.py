#!/usr/bin/env python3
"""본인 터미널에서만 API 키를 입력받아 권한 600의 .env로 저장합니다."""

import getpass
import os
from pathlib import Path


def main():
    path = Path(__file__).resolve().parent / ".env"
    print("API 키는 이 터미널에만 붙여 넣으세요. 입력한 내용은 화면에 표시되지 않습니다.")
    print("각 키는 한 번만 붙여 넣고 Enter를 누르세요. 글자가 안 보여도 다시 붙여 넣지 마세요.")
    print("채팅이나 GitHub에 키를 보내지 마세요. 취소하려면 Ctrl+C를 누르세요.")
    if path.exists():
        answer = input("기존 .env 설정을 새 키로 바꾸려면 yes를 입력하세요: ").strip()
        if answer != "yes":
            print("설정을 그대로 두었습니다.")
            return
    gemini = getpass.getpass("Gemini API 키: ").strip()
    kakao = getpass.getpass("Kakao REST API 키: ").strip()
    if not gemini or not kakao or any(c in gemini + kakao for c in "\r\n\"'"):
        print("빈 키 또는 올바르지 않은 값입니다. 파일을 저장하지 않았습니다.")
        return
    # 파일을 만드는 순간부터 소유자만 읽고 쓸 수 있게 합니다.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.chmod(path, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(f"GEMINI_API_KEY={gemini}\nKAKAO_REST_API_KEY={kakao}\nGEMINI_MODEL=gemini-3.1-flash-lite\n")
    print("설정 완료! .env에 저장했습니다. 키 값은 출력하지 않습니다.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n설정을 취소했습니다.")
