import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 内置代理池
BUILTIN_PROXIES = [
    "http://46.62.171.144:80",
    "http://18.202.158.161:80",
    "http://45.4.202.170:999",
    "http://200.59.186.176:999",
    "http://5.202.176.42:80",
    "http://134.209.29.120:8080",
    "http://103.30.211.34:80",
    "http://8.213.195.191:3333",
    "http://8.220.204.215:8086",
    "http://47.91.89.3:8081",
    "http://8.211.195.139:8081",
    "http://62.99.135.51:80",
    "http://87.239.31.42:80",
    "http://8.137.62.53:8081",
    "http://8.243.68.11:8080",
    "http://47.121.183.107:9080",
    "http://154.31.113.209:80",
    "http://200.33.20.25:80",
    "http://94.184.25.4:80",
    "http://47.91.89.3:1081",
    "http://38.54.9.151:3128",
    "http://47.91.89.3:6379",
    "http://103.253.43.144:80",
    "http://190.116.28.148:80",
    "http://8.211.51.115:4022",
    "http://188.245.91.223:80",
]

def test_proxy(proxy_url):
    """测试单个代理是否可用"""
    try:
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # 测试访问 qushuiyin.me
        response = requests.get(
            'https://qushuiyin.me/',
            proxies=proxies,
            timeout=10,
            verify=False
        )
        
        # 检查响应
        if response.status_code == 200:
            content = response.text.lower()
            # 检查是否是正确的页面
            if 'sora' in content or 'qushuiyin' in content:
                return {
                    'proxy': proxy_url,
                    'status': '✓ 可用',
                    'code': response.status_code,
                    'valid': True
                }
            else:
                return {
                    'proxy': proxy_url,
                    'status': '✗ 页面错误',
                    'code': response.status_code,
                    'valid': False,
                    'reason': '返回了错误页面'
                }
        else:
            return {
                'proxy': proxy_url,
                'status': '✗ 状态码错误',
                'code': response.status_code,
                'valid': False
            }
    except requests.exceptions.Timeout:
        return {
            'proxy': proxy_url,
            'status': '✗ 超时',
            'valid': False,
            'reason': '连接超时'
        }
    except requests.exceptions.ProxyError:
        return {
            'proxy': proxy_url,
            'status': '✗ 代理错误',
            'valid': False,
            'reason': '代理无法连接'
        }
    except Exception as e:
        return {
            'proxy': proxy_url,
            'status': f'✗ 错误: {type(e).__name__}',
            'valid': False,
            'reason': str(e)[:50]
        }

def main():
    print("开始测试代理池...")
    print(f"总共 {len(BUILTIN_PROXIES)} 个代理\n")
    
    results = []
    valid_proxies = []
    
    # 使用线程池并发测试
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in BUILTIN_PROXIES}
        
        for i, future in enumerate(as_completed(future_to_proxy), 1):
            result = future.result()
            results.append(result)
            
            print(f"[{i}/{len(BUILTIN_PROXIES)}] {result['proxy']}")
            print(f"    状态: {result['status']}")
            if 'reason' in result:
                print(f"    原因: {result['reason']}")
            print()
            
            if result['valid']:
                valid_proxies.append(result['proxy'])
    
    # 输出总结
    print("=" * 60)
    print(f"测试完成！")
    print(f"可用代理: {len(valid_proxies)}/{len(BUILTIN_PROXIES)}")
    print("=" * 60)
    
    if valid_proxies:
        print("\n✓ 可用的代理列表：")
        for proxy in valid_proxies:
            print(f"    \"{proxy}\",")
    else:
        print("\n✗ 没有找到可用的代理")
    
    # 保存结果到文件
    with open('proxy_test_results.txt', 'w', encoding='utf-8') as f:
        f.write(f"代理测试结果 - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"可用代理: {len(valid_proxies)}/{len(BUILTIN_PROXIES)}\n\n")
        
        if valid_proxies:
            f.write("可用代理列表:\n")
            for proxy in valid_proxies:
                f.write(f"    \"{proxy}\",\n")
            f.write("\n")
        
        f.write("详细测试结果:\n")
        for result in results:
            f.write(f"\n{result['proxy']}\n")
            f.write(f"  状态: {result['status']}\n")
            if 'reason' in result:
                f.write(f"  原因: {result['reason']}\n")
    
    print(f"\n结果已保存到 proxy_test_results.txt")

if __name__ == "__main__":
    # 禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    main()
