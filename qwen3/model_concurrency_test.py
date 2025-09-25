import asyncio
import time
import json
import statistics
from typing import List, Dict, Optional
import argparse
import os
import re

import aiohttp
from dotenv import load_dotenv

"""
单测

python3 qwen3/modelhandler_concurrency_test.py \
  --base-url http://127.0.0.1:8888 \
  --route /mall_ai_model/question \
  --place-id 801 \
  --token G2GJV8RPoUh35000 \
  --mode 单测 \
  --prompt "你是什么模型"

并发

python3 qwen3/model_concurrency_test.py \
  --base-url https://screen.aibee.cn \
  --route /demo_ai_model/question \
  --place-id 801 \
  --token G200000000000000 \
  --mode 并发 \
  --count 1 \
  --concurrency 1
"""

load_dotenv()
model_name = os.environ.get("MODEL_NAME", "Qwen3-8B-FP8")

class ModelHandlerConcurrencyTester:
    """对 Tornado 的 ModelHandler 进行并发测试的工具。

    - 默认路由: /demo_ai_model/question（与 main.py 的默认 APP_ENV 对应）
    - 通过 place_id 与 token/uni_token 来通过登录校验：
      * place_id=720 时使用 uni_token 作为 user_id
      * 其他 place_id 则使用 token 作为 user_id（801 需要有效 token）
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8888",
        route: str = "/demo_ai_model/question",
        place_id: int = 720,
        token: str = "",
        session_prefix: str = "test-session",
        intention: Optional[str] = None,
        request_timeout: float = 60.0,
        count: int = 10,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        if not route.startswith("/"):
            route = "/" + route
        self.route = route
        self.url = f"{self.base_url}{self.route}"

        self.place_id = place_id
        self.token = token
        self.session_prefix = session_prefix
        self.intention = intention
        self.request_timeout = request_timeout
        self.token_queue = asyncio.Queue()
        self.count = count

    async def _initialize_token_queue(self, count):
        for i in range(count):
            modified_token = self._increment_token(self.token, i + 1)
            await self.token_queue.put(modified_token)

    def _build_headers(self, request_id: int) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "session_id": f"{self.session_prefix}-{request_id}",
            "token": self.token or "test_token",
        }
        if self.intention:
            headers["intention"] = self.intention
        return headers

    def _build_body(self, user_input: str) -> Dict:
        return {
            "place_id": self.place_id,
            "user_input": user_input,
        }

    async def _read_sse_response(self, resp: aiohttp.ClientResponse) -> str:
        # 逐块读取 SSE 文本，直到服务端关闭连接
        text_parts: List[str] = []
        async for chunk in resp.content.iter_chunked(1024):
            try:
                text_parts.append(chunk.decode("utf-8", errors="ignore"))
            except Exception:
                # 忽略解码异常的块
                continue
        return "".join(text_parts)

    async def single_request(self, session: aiohttp.ClientSession, prompt: str, request_id: int) -> Dict:
        # 记录请求开始时间
        request_start_time = time.time()
        self.token = await self.token_queue.get()
        try:
            headers = self._build_headers(request_id)
            body = self._build_body(prompt)

            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            async with session.post(self.url, headers=headers, json=body, timeout=timeout) as resp:
                print(headers.get("token"))
                if resp.status != 200:
                    # 读取文本帮助定位错误
                    try:
                        err_text = await resp.text()
                    except Exception:
                        err_text = ""
                    return {
                        "request_id": request_id,
                        "status": "http_error",
                        "http_status": resp.status,
                        "error": err_text,
                    }

                # 记录响应开始时间
                response_start_time = time.time()
                # 读取 SSE 全量文本直到结束
                content_text = await self._read_sse_response(resp)
                pattern = r'data: \{"msg": "([^"]+)"\}'
                matches = re.findall(pattern, content_text)

                # 拼接所有msg内容为一句话
                content_text = ''.join(matches)
                # 记录响应结束时间
                response_end_time = time.time()

                # 首字回复时间 = 响应开始时间 - 请求开始时间
                first_response_time = response_start_time - request_start_time
                # 回复持续时间 = 响应结束时间 - 响应开始时间
                duration_response_time = response_end_time - response_start_time
                # 每秒回复token数量 = 回复token数量 / 回复持续时间
                output_length = len(content_text)
                response_tokens_ps = output_length / duration_response_time if duration_response_time > 0 else 0

                return {
                    "request_id": request_id,
                    "status": "success",
                    "request_start_time": request_start_time,
                    "first_response_time": first_response_time,
                    "duration_response_time": duration_response_time,
                    "response_tokens_ps": response_tokens_ps,
                    "response_length": len(content_text),
                }
        except Exception as e:
            print(e)
            return {
                "request_id": request_id,
                "status": "error",
                "error": str(e),
            }

    async def concurrent_test(self, prompts: List[str], max_concurrent: int = 10) -> Dict:
        print(f"开始并发测试，最大并发数: {max_concurrent}")
        print(f"目标地址: {self.url}")
        print(f"总请求数: {len(prompts)}")

        # 记录并发开始时间
        concurrency_start_time = time.time()
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited(prompt: str, request_id: int, session: aiohttp.ClientSession):
            async with semaphore:
                return await self.single_request(session, prompt, request_id)

        async with aiohttp.ClientSession() as session:
            await self._initialize_token_queue(self.count)
            tasks = []
            for i, prompt in enumerate(prompts):
                task = limited(prompt, i, session)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=False)

        # 记录并发结束的时间
        concurrency_end_time = time.time()

        # 记录成功请求数量
        successful_requests = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
        # 记录失败请求数量
        failed_requests = [r for r in results if isinstance(r, dict) and r.get("status") != "success"]

        if successful_requests:
            # 首字回复时间
            first_response_time = [r["first_response_time"] for r in successful_requests]
            # 回复持续时间
            duration_response_time = [r["duration_response_time"] for r in successful_requests]
            # 每秒回复token数量
            response_tokens_ps = [r["response_tokens_ps"] for r in successful_requests]

            # 平均 / 最快 / 最慢 / 所有 首字回复时间
            avg_first_response_time = statistics.mean(first_response_time)
            min_first_response_time = min(first_response_time)
            max_first_response_time = max(first_response_time)

            # 平均 / 最快 / 最慢 回复持续时间
            avg_duration_response_time = statistics.mean(duration_response_time)
            min_duration_response_time = min(duration_response_time)
            max_duration_response_time = max(duration_response_time)
            # 并发到所有回复完成总耗时
            concurrency_full_response_time = concurrency_end_time - concurrency_start_time

            # 平均 / 最快 / 最慢 每秒回复token数量
            avg_response_tokens_ps = statistics.mean(response_tokens_ps)
            min_response_tokens_ps = min(response_tokens_ps)
            max_response_tokens_ps = max(response_tokens_ps)

        else:
            avg_first_response_time = min_first_response_time = max_first_response_time = 0.0

        request_start_time = [r.get("request_start_time") for r in results if r.get("request_start_time") is not None]
        if request_start_time:
            # 计算所有请求全部发出的总时间
            all_request_time = max(request_start_time) - concurrency_start_time

        # 返回并发测试指标
        return {
            "total_requests": len(prompts),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": (len(successful_requests) / len(prompts) * 100.0) if prompts else 0.0,

            # 平均 / 最快 / 最慢 首字回复时间
            "avg_first_response_time": avg_first_response_time,
            "min_first_response_time": min_first_response_time,
            "max_first_response_time": max_first_response_time,

            # 平均 / 最快 / 最慢 回复持续时间
            "avg_duration_response_time": avg_duration_response_time,
            "min_duration_response_time": min_duration_response_time,
            "max_duration_response_time": max_duration_response_time,
            # 并发到所有回复完成总耗时
            "concurrency_full_response_time": concurrency_full_response_time,

            # 平均 / 最少 / 最多 每秒回复token数量
            "avg_response_tokens_ps": avg_response_tokens_ps,
            "min_response_tokens_ps": min_response_tokens_ps,
            "max_response_tokens_ps": max_response_tokens_ps,

            # 所有请求全部发出的总时间
            "all_request_time": all_request_time,

            "max_concurrent": max_concurrent,
        }, results

    @staticmethod
    def generate_test_prompts(count: int = 20) -> List[str]:
        base_prompts = [
            # "你好"
            "会员权益"
            # "买裤子"
        ]
        prompts: List[str] = []
        for i in range(count):
            prompts.append(f"{base_prompts[i % len(base_prompts)]}")
        return prompts

    def _increment_token(self, token, request_count):
        # 提取 token 中的数字部分
        prefix = ''.join(filter(lambda x: not x.isdigit(), token))
        number_part = ''.join(filter(lambda x: x.isdigit(), token))
        
        # 将数字部分转换为整数，并加上 request_count
        new_number_part = int(number_part) + request_count
        
        # 将新的数字部分转换回字符串，并拼接回原始格式
        new_token = prefix + str(new_number_part).zfill(len(number_part))
        return new_token

    @staticmethod
    def print_results(summary: Dict, results: List[Dict]) -> None:
        print("\n" + "=" * 60)
        print(f"{model_name} 并发测试结果")
        print("=" * 60)
        print(f"总请求数: {summary['total_requests']}")
        print(f"成功请求数: {summary['successful_requests']}")
        print(f"失败请求数: {summary['failed_requests']}")
        print(f"成功率: {summary['success_rate']:.2f}%")

        print(f"平均首字回复时间: {summary['avg_first_response_time']:.2f}秒")
        print(f"最快首字回复时间: {summary['min_first_response_time']:.2f}秒")
        print(f"最慢首字回复时间: {summary['max_first_response_time']:.2f}秒")

        print(f"平均回复持续时间: {summary['avg_duration_response_time']:.2f}秒")
        print(f"最快回复持续时间: {summary['min_duration_response_time']:.2f}秒")
        print(f"最慢回复持续时间: {summary['max_duration_response_time']:.2f}秒")
        print(f"并发到所有回复完成总耗时: {summary['concurrency_full_response_time']:.2f}秒")

        print(f"平均每秒回复token数量: {summary['avg_response_tokens_ps']:.2f}")
        print(f"最少每秒回复token数量: {summary['min_response_tokens_ps']:.2f}")
        print(f"最多每秒回复token数量: {summary['max_response_tokens_ps']:.2f}")

        print(f"所有请求全部发出的总时间: {summary['all_request_time']:.5f}秒")

        if summary["failed_requests"] > 0:
            print("\n失败请求示例(最多展示前5条):")
            shown = 0
            for r in results:
                if isinstance(r, dict) and r.get("status") != "success":
                    print(json.dumps(r, ensure_ascii=False)[:500])
                    shown += 1
                    if shown >= 5:
                        break

    @staticmethod
    def save_results_to_file(summary: Dict, results: List[Dict], filename: str) -> None:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"# {model_name} 并发测试结果\n\n")

            f.write(f"总请求数: {summary['total_requests']}\n")
            f.write(f"成功请求数: {summary['successful_requests']}\n")
            f.write(f"失败请求数: {summary['failed_requests']}\n")
            f.write(f"成功率: {summary['success_rate']:.2f}%\n")

            f.write(f"平均首字回复时间: {summary['avg_first_response_time']:.2f}秒\n")
            f.write(f"最快首字回复时间: {summary['min_first_response_time']:.2f}秒\n")
            f.write(f"最慢首字回复时间: {summary['max_first_response_time']:.2f}秒\n")

            f.write(f"平均回复持续时间: {summary['avg_duration_response_time']:.2f}秒\n")
            f.write(f"最快回复持续时间: {summary['min_duration_response_time']:.2f}秒\n")
            f.write(f"最慢回复持续时间: {summary['max_duration_response_time']:.2f}秒\n")
            f.write(f"并发到所有回复完成总耗时: {summary['concurrency_full_response_time']:.2f}秒\n")

            f.write(f"平均每秒回复token数量: {summary['avg_response_tokens_ps']:.2f}\n")
            f.write(f"最少每秒回复token数量: {summary['min_response_tokens_ps']:.2f}\n")
            f.write(f"最多每秒回复token数量: {summary['max_response_tokens_ps']:.2f}\n")

            f.write(f"所有请求全部发出的总时间: {summary['all_request_time']:.5f}秒\n\n")

            if summary["failed_requests"] > 0:
                f.write("## 失败请求示例(最多展示前5条)\n")
                shown = 0
                for r in results:
                    if isinstance(r, dict) and r.get("status") != "success":
                        f.write(json.dumps(r, ensure_ascii=False)[:500] + "\n\n")
                        shown += 1
                        if shown >= 5:
                            break


async def main_async(args: argparse.Namespace) -> None:
    tester = ModelHandlerConcurrencyTester(
        base_url=args.base_url,
        route=args.route,
        place_id=args.place_id,
        token=args.token,
        session_prefix=args.session_prefix,
        intention=args.intention,
        request_timeout=args.timeout,
        count=args.count,
    )

    if args.mode == "单测":
        prompts = [args.prompt or "你好，请介绍一下自己"]
        async with aiohttp.ClientSession() as session:
            result = await tester.single_request(session, prompts[0], 1)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        prompts = tester.generate_test_prompts(args.count)
        summary, results = await tester.concurrent_test(prompts, args.concurrency)
        tester.print_results(summary, results)
        tester.save_results_to_file(summary, results, f"qwen3/model_concurrency_test_{model_name}.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ModelHandler 并发测试脚本")
    parser.add_argument("--base-url", default="http://127.0.0.1:8888", help="服务基础 URL，如 http://127.0.0.1:8888")
    parser.add_argument("--route", default="/demo_ai_model/question", help="目标路由，如 /demo_ai_model/question | /ai_model/question | /mall_ai_model/question")
    parser.add_argument("--place-id", type=int, default=720, help="place_id，720 使用 uni_token 作为 user_id")
    parser.add_argument("--token", default="", help="header: token，place_id 非 720 时建议提供")
    parser.add_argument("--session-prefix", default="test-session", help="session_id 前缀")
    parser.add_argument("--intention", default=None, help="可选的 intention 请求头")
    parser.add_argument("--timeout", type=float, default=60.0, help="单个请求超时(秒)")

    parser.add_argument("--mode", choices=["单测", "并发"], default="并发", help="运行模式：单测/并发")
    parser.add_argument("--prompt", default="", help="单测模式下的提示词")
    parser.add_argument("--count", type=int, default=20, help="并发总请求数")
    parser.add_argument("--concurrency", type=int, default=5, help="最大并发数")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()