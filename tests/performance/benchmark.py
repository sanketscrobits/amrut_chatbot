"""
Performance benchmarking for AMRUT Chatbot
Measures response times for all operations
"""
import requests
import time
import statistics
from pathlib import Path

BASE_URL = "http://localhost:8000"

def benchmark_operation(name, func, iterations=10):
    """Benchmark a single operation"""
    times = []
    successes = 0
    
    print(f"\n🔄 Benchmarking: {name} ({iterations} iterations)")
    
    for i in range(iterations):
        start = time.time()
        try:
            success = func()
            elapsed = time.time() - start
            times.append(elapsed)
            if success:
                successes += 1
            print(f"  Run {i+1}: {elapsed:.2f}s {'✅' if success else '❌'}")
        except Exception as e:
            print(f"  Run {i+1}: ERROR - {e}")
    
    if times:
        return {
            'name': name,
            'iterations': iterations,
            'successes': successes,
            'success_rate': (successes / iterations) * 100,
            'times': times,
            'min': min(times),
            'max': max(times),
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'p95': sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0],
        }
    return None


def test_health_check():
    response = requests.get(f"{BASE_URL}/")
    return response.status_code == 200


def test_document_upload():
    content = "# Test Document\n\nThis is a test document for benchmarking."
    with open('/tmp/bench_test.md', 'w') as f:
        f.write(content)
    
    with open('/tmp/bench_test.md', 'rb') as f:
        files = {'file': ('bench_test.md', f, 'text/markdown')}
        response = requests.post(
            f"{BASE_URL}/upload/bench_test_{int(time.time())}",
            files=files
        )
    return response.status_code == 200


def test_simple_query():
    response = requests.post(
        f"{BASE_URL}/chatbot",
        json={"user_message": "Hello, how are you?"}
    )
    return response.status_code == 200


def test_document_query():
    response = requests.post(
        f"{BASE_URL}/chatbot",
        json={"user_message": "What is the data encryption policy?"}
    )
    return response.status_code == 200


def main():
    print("="*80)
    print("AMRUT CHATBOT - PERFORMANCE BENCHMARKS")
    print("="*80)
    
    results = []
    
    # Benchmark each operation
    results.append(benchmark_operation("Health Check", test_health_check, 20))
    results.append(benchmark_operation("Document Upload", test_document_upload, 5))
    results.append(benchmark_operation("Simple Query", test_simple_query, 10))
    results.append(benchmark_operation("Document Query", test_document_query, 10))
    
    # Print summary
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY")
    print("="*80)
    
    print(f"\n{'Operation':<25} {'Success Rate':<15} {'Mean':<10} {'Median':<10} {'P95':<10}")
    print("-" * 80)
    
    for result in results:
        if result:
            print(f"{result['name']:<25} "
                  f"{result['success_rate']:>6.1f}% {'':<7} "
                  f"{result['mean']:>7.2f}s  "
                  f"{result['median']:>7.2f}s  "
                  f"{result['p95']:>7.2f}s")
    
    # Performance assessment
    print("\n" + "="*80)
    print("PERFORMANCE ASSESSMENT")
    print("="*80)
    
    for result in results:
        if result and result['mean'] > 0:
            if result['mean'] < 1.0:
                rating = "✅ Excellent"
            elif result['mean'] < 3.0:
                rating = "✅ Good"
            elif result['mean'] < 5.0:
                rating = "⚠️  Acceptable"
            else:
                rating = "❌ Slow"
            
            print(f"{result['name']:<30} {rating}")
    
    print("\n" + "="*80)
    print("BENCHMARK COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
