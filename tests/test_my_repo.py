#!/usr/bin/env python3
"""
사용자 repository의 최신 commit 기준 지정된 일수간 commit 조회 테스트
최신 commit 날짜부터 역순으로 N일간의 commit을 분석합니다.
Usage: python test_my_repo.py <owner/repo> [--days N]
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add src to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
from infrastructure.github_client import GitHubAPIClient

def test_repository_commits(repository: str, days: int = 3):
    """실제 repository에서 최신 commit 기준 지정된 일수의 commit 조회 테스트"""
    
    # Repository 형식 검증 (owner/repo)
    if '/' not in repository:
        print(f"❌ Repository 형식이 올바르지 않습니다. 'owner/repo' 형식으로 입력해주세요.")
        print(f"   예: microsoft/vscode, facebook/react")
        return
    
    owner, repo = repository.split('/', 1)
    
    print(f"\n🔍 Testing repository: {owner}/{repo}")
    print("=" * 50)
    
    try:
        with GitHubAPIClient() as client:
            # Repository 정보 조회
            repo_endpoint = f"/repos/{owner}/{repo}"
            repo_result = client.http_client.get(repo_endpoint)
            
            if repo_result.is_ok():
                repo_data = repo_result.unwrap()
                print(f"✅ Repository info:")
                print(f"   Name: {repo_data.get('full_name', 'Unknown')}")
                print(f"   Description: {repo_data.get('description') or 'No description'}")
                print(f"   Language: {repo_data.get('language') or 'Unknown'}")
                print(f"   Stars: {repo_data.get('stargazers_count', 0)}")
                print(f"   Updated: {repo_data.get('updated_at', 'Unknown')}")
            else:
                error = repo_result.unwrap_err()
                print(f"❌ Repository info failed: {getattr(error, 'message', str(error))}")
                return
            
            # 1단계: 최신 commit 날짜 조회
            print("\n🔍 최신 commit 날짜 확인 중...")
            latest_commit_endpoint = f"/repos/{owner}/{repo}/commits"
            latest_result = client.http_client.get(latest_commit_endpoint, params={'per_page': 1})
            
            if not latest_result.is_ok():
                error = latest_result.unwrap_err()
                print(f"❌ Latest commit query failed: {getattr(error, 'message', str(error))}")
                return
            
            latest_commits = latest_result.unwrap()
            if not latest_commits:
                print("❌ Repository에 commit이 없습니다.")
                return
            
            # 최신 commit 날짜 파싱
            latest_commit = latest_commits[0]
            latest_date_str = latest_commit['commit']['author']['date']
            latest_date = datetime.fromisoformat(latest_date_str.replace('Z', '+00:00'))
            
            print(f"✅ 최신 commit: {latest_date.strftime('%Y-%m-%d %H:%M')} ({latest_commit['sha'][:8]})")
            print(f"   Message: {latest_commit['commit']['message'][:50]}...")
            
            # 2단계: 최신 commit 날짜부터 n일 전까지의 commit 조회
            since_date = latest_date - timedelta(days=days)
            since_str = since_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            until_str = latest_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            print(f"\n📅 조회 기간: {since_date.strftime('%Y-%m-%d')} ~ {latest_date.strftime('%Y-%m-%d')} ({days}일간)")
            
            commits_endpoint = f"/repos/{owner}/{repo}/commits"
            params = {'since': since_str, 'until': until_str, 'per_page': 50}
            commits_result = client.http_client.get(commits_endpoint, params=params)
            
            if commits_result.is_ok():
                commits = commits_result.unwrap()
                print(f"\n📝 Recent commits (last {days} days): {len(commits)} commits")
                
                if commits:
                    for i, commit_data in enumerate(commits[:5]):  # 최대 5개만 표시
                        commit_date = datetime.fromisoformat(
                            commit_data['commit']['author']['date'].replace('Z', '+00:00')
                        ).strftime('%Y-%m-%d %H:%M')
                        
                        print(f"   [{i+1}] {commit_data['sha'][:8]} - {commit_date}")
                        print(f"       Author: {commit_data['commit']['author']['name']}")
                        print(f"       Message: {commit_data['commit']['message'][:60]}...")
                        
                        # 개별 commit 상세 정보 조회
                        commit_detail_endpoint = f"/repos/{owner}/{repo}/commits/{commit_data['sha']}"
                        detail_result = client.http_client.get(commit_detail_endpoint)
                        
                        if detail_result.is_ok():
                            detail = detail_result.unwrap()
                            if 'files' in detail:
                                files = detail['files']
                                total_additions = sum(f.get('additions', 0) for f in files)
                                total_deletions = sum(f.get('deletions', 0) for f in files)
                                print(f"       Files: {len(files)} changed (+{total_additions} -{total_deletions})")
                                
                                # 변경된 파일 유형 분석 (최대 3개 파일만)
                                for file in files[:3]:
                                    filename = file.get('filename', 'unknown')
                                    additions = file.get('additions', 0)
                                    deletions = file.get('deletions', 0)
                                    print(f"         • {filename} (+{additions} -{deletions})")
                        print()  # 빈 줄 추가
                        
                else:
                    print(f"   📭 이 기간({since_date.strftime('%Y-%m-%d')} ~ {latest_date.strftime('%Y-%m-%d')})에는 commit이 없습니다.")
                    print(f"   💡 더 긴 기간을 원하시면 --days 값을 늘려보세요.")
            else:
                error = commits_result.unwrap_err()
                print(f"❌ Commits query failed: {getattr(error, 'message', str(error))}")
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def parse_arguments():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(
        description="GitHub repository의 최신 commit 기준으로 지정된 일수간의 commit을 조회합니다.",
        epilog="예시: python test_my_repo.py microsoft/vscode --days 7"
    )
    
    parser.add_argument(
        "repository",
        help="조회할 repository (owner/repo 형식, 예: microsoft/vscode)"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=3,
        help="조회할 일수 (기본값: 3일)"
    )
    
    return parser.parse_args()

def main():
    """메인 함수"""
    args = parse_arguments()
    
    print("🚀 Repository Commit 조회 테스트 시작")
    
    # Load environment variables
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ .env 파일 로드됨")
    else:
        print("❌ .env 파일을 찾을 수 없습니다")
        return 1
    
    # Check if token exists
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN이 설정되지 않았습니다")
        return 1
    
    print(f"✅ GitHub 토큰 확인됨 (길이: {len(token)})")
    print("=" * 70)
    
    test_repository_commits(args.repository, args.days)
    
    print("=" * 70)
    print("🎯 테스트 완료!")
    return 0

if __name__ == "__main__":
    exit(main())