# GitHub Commit Analyzer MCP 서버 DSL 설계 (Claude Code 연동)
**아키텍처**: 함수형 파이프라인 기반 선언적 설계

## 1. 함수형 아키텍처 원칙

```dsl
architecture FunctionalPipeline {
    paradigm: "함수형 프로그래밍"
    patterns: [
        "순수 함수 (Pure Functions)",
        "불변성 (Immutability)", 
        "함수 합성 (Function Composition)",
        "파이프라인 처리 (Pipeline Processing)",
        "선언적 규칙 (Declarative Rules)"
    ]
    
    design_principles: {
        immutability: "모든 데이터 구조는 불변"
        pure_functions: "부작용 없는 순수 함수"
        composition: "작은 함수들의 조합으로 복잡한 로직 구성"
        declarative: "무엇을 할지 선언, 어떻게 할지는 추상화"
        testability: "각 함수 독립적 테스트 가능"
    }
}
```

## 2. 시스템 아키텍처

```dsl
system Architecture {
    type: MCP_Server
    client: Claude_Code
    protocol: JSON_RPC_2.0
    transport: STDIO
    
    capabilities: [
        Tools,
        Logging,
        Progress_Reporting
    ]
    
    external_apis: [
        GitHub_REST_API,
        OpenRouter_API
    ]
    
    deployment: Local_Development_Environment
}
```

## 2. MCP 서버 구성

```dsl
server GitHubCommitAnalyzer {
    name: "github-commit-analyzer"
    version: "1.0.0"
    description: "GitHub 리포지토리 커밋 분석 및 AI 인사이트 생성 도구"
    
    initialization {
        protocol_version: "2024-11-05"
        capabilities: {
            tools: true
            logging: true
            progress: true
        }
    }
    
    runtime {
        transport: STDIO
        error_handling: Graceful_Degradation
        rate_limiting: GitHub_API_Limits
        memory_management: Stateless
    }
}
```

## 3. 도구(Tools) 정의

```dsl
module Tools {
    
    tool AnalyzeCommits {
        name: "analyze_commits"
        description: "GitHub 리포지토리의 최근 코드 변경사항을 분석합니다"
        
        parameters: {
            owner: {
                type: String
                description: "리포지토리 소유자 (GitHub 사용자명 또는 조직명)"
                required: true
                pattern: "^[a-zA-Z0-9-_.]+$"
            }
            repo: {
                type: String
                description: "리포지토리 이름"
                required: true
                pattern: "^[a-zA-Z0-9-_.]+$"
            }
            days: {
                type: Integer
                description: "분석할 기간 (일 단위)"
                default: 7
                minimum: 1
                maximum: 30
            }
        }
        
        output: {
            type: "formatted_analysis_report"
            format: "markdown"
            sections: [
                "전체_통계",
                "주요_기여자", 
                "코드_작업_유형_분석",
                "주요_변경_파일"
            ]
        }
        
        claude_code_usage: [
            "facebook/react 리포지토리 분석해줘",
            "microsoft/vscode 최근 14일간 코드 변경 분석해줘",
            "owner/repo 프로젝트 최근 작업 내용 분석해줘"
        ]
    }
    
    tool GetCommitDiff {
        name: "get_commit_diff"
        description: "특정 커밋의 상세 변경사항(diff)을 조회합니다"
        
        parameters: {
            owner: {
                type: String
                description: "리포지토리 소유자"
                required: true
            }
            repo: {
                type: String
                description: "리포지토리 이름"
                required: true
            }
            commit_sha: {
                type: String
                description: "커밋 SHA (해시값)"
                required: true
                pattern: "^[a-f0-9]{7,40}$"
            }
        }
        
        output: {
            type: "diff_content"
            format: "markdown_code_block"
            size_limit: 5000_characters
            fallback: "summary_with_github_link"
        }
        
        claude_code_usage: [
            "facebook/react 커밋 abc1234의 변경사항 보여줘",
            "특정 커밋 a1b2c3d4 diff 내용 확인해줘"
        ]
    }
    
    tool RepositorySummary {
        name: "repository_summary"
        description: "GitHub 리포지토리의 기본 정보와 최근 활동을 요약합니다"
        
        parameters: {
            owner: {
                type: String
                description: "리포지토리 소유자"
                required: true
            }
            repo: {
                type: String
                description: "리포지토리 이름"
                required: true
            }
        }
        
        output: {
            type: "repository_overview"
            format: "structured_markdown"
            sections: [
                "기본_정보",
                "최근_활동",
                "링크"
            ]
        }
        
        claude_code_usage: [
            "vercel/next.js 리포지토리 정보 요약해줘",
            "sveltejs/svelte 프로젝트 개요 알려줘"
        ]
    }
    
    tool AnalyzeCodeChanges {
        name: "analyze_code_changes"
        description: "커밋의 실제 코드 변경사항을 분석하여 작업 내용을 상세히 파악합니다"
        
        parameters: {
            owner: {
                type: String
                description: "리포지토리 소유자"
                required: true
            }
            repo: {
                type: String
                description: "리포지토리 이름"
                required: true
            }
            days: {
                type: Integer
                description: "분석할 기간 (일 단위)"
                default: 7
                minimum: 1
                maximum: 30
            }
            deep_analysis: {
                type: Boolean
                description: "상세 코드 분석 수행 여부"
                default: true
            }
        }
        
        output: {
            type: "code_analysis_report"
            format: "structured_markdown"
            sections: [
                "파일별_변경_통계",
                "코드_복잡도_변화",
                "주요_함수_클래스_변경",
                "의존성_변경",
                "작업_유형_분석"
            ]
        }
        
        features: {
            file_statistics: {
                added_lines: "추가된 라인 수",
                deleted_lines: "삭제된 라인 수",
                modified_files: "수정된 파일 목록",
                file_types: "변경된 파일 타입별 분류"
            }
            
            complexity_analysis: {
                cyclomatic_complexity: "순환 복잡도 변화",
                cognitive_complexity: "인지 복잡도 변화",
                method_length: "메서드 길이 변화"
            }
            
            structural_changes: {
                new_functions: "새로 추가된 함수/메서드",
                modified_functions: "수정된 함수/메서드",
                deleted_functions: "삭제된 함수/메서드",
                class_changes: "클래스 구조 변경사항"
            }
            
            dependency_tracking: {
                new_imports: "새로 추가된 의존성",
                removed_imports: "제거된 의존성",
                package_updates: "패키지 버전 변경"
            }
        }
        
        claude_code_usage: [
            "facebook/react의 코드 변경사항 깊이 분석해줘",
            "최근 7일간 어떤 코드 작업이 있었는지 상세히 알려줘",
            "코드 복잡도가 어떻게 변했는지 분석해줘"
        ]
    }
}
```

## 4. 함수형 데이터 처리 파이프라인

```dsl
module FunctionalDataPipeline {
    
    // 주요 분석 파이프라인
    pipeline AnalyzeRepositoryPipeline {
        composition: [
            validateInput,
            fetchGitHubData,
            extractDiffs,
            analyzeFileChanges,
            inferWorkTypes,
            calculateMetrics,
            formatReport
        ]
        
        type_signature: "RepoParams -> Result<AnalysisReport>"
        
        error_handling: "함수형 Result 타입으로 모나딕 처리"
    }
    
    // 순수 함수 정의
    pure_functions: {
        // 입력 검증 (순수)
        validateInput: "RepoParams -> Either<ValidationError, ValidParams>"
        
        // 데이터 변환 (순수)
        extractDiffs: "GitHubResponse -> List<DiffData>"
        analyzeFileChanges: "List<DiffData> -> List<FileChange>"
        inferWorkTypes: "List<FileChange> -> List<WorkType>"
        calculateMetrics: "List<WorkType> -> Metrics"
        formatReport: "AnalysisData -> MarkdownReport"
        
        // 규칙 적용 (순수)
        applyWorkTypeRules: "List<Rule> -> FileChange -> List<WorkType>"
        applyWorkStatusRules: "List<Rule> -> List<FileChange> -> WorkStatus"
    }
    
    // 부작용 함수 (I/O 경계)
    side_effect_functions: {
        fetchGitHubData: "ValidParams -> IO<Result<GitHubResponse>>"
        logAnalysisEvent: "AnalysisEvent -> IO<Unit>"
        cacheResult: "CacheKey -> AnalysisResult -> IO<Unit>"
    }
    
    service GitHubAPIClient {
        description: "I/O 경계층 - 부작용 격리"
        base_url: "https://api.github.com"
        authentication: Personal_Access_Token
        rate_limit: 5000_requests_per_hour
        
        functions: [
            getRepositoryInfo: "RepoIdentifier -> IO<Result<RepositoryData>>",
            getRecentCommits: "RepoIdentifier -> TimeRange -> IO<Result<List<CommitData>>>",
            getCommitDiff: "CommitIdentifier -> IO<Result<DiffContent>>"
        ]
        
        error_handling: {
            pattern: "Result<T> 타입으로 함수형 에러 처리"
            rate_limit_exceeded: "ExponentialBackoff monad"
            not_found: "Left(NotFoundError)"
            unauthorized: "Left(AuthError)"
            network_error: "Left(NetworkError)"
        }
    }
    
    // 선언적 규칙 엔진
    declarative_rules: {
        // 작업 유형 추론 규칙
        work_type_rules: [
            Rule {
                name: "test_work"
                condition: file_path_matches(["*.test.*", "*.spec.*", "__tests__/*"])
                output: WorkType.Testing
            },
            Rule {
                name: "documentation"
                condition: file_path_matches(["*.md", "docs/*", "README*"])
                output: WorkType.Documentation
            },
            Rule {
                name: "configuration"
                condition: file_path_matches(["*.config.*", "*.json", "*.yml"])
                output: WorkType.Configuration
            },
            Rule {
                name: "feature_development"
                condition: and(
                    file_path_matches(["src/*", "components/*", "pages/*"]),
                    lines_changed_greater_than(10)
                )
                output: WorkType.FeatureDevelopment
            },
            Rule {
                name: "bug_fix"
                condition: and(
                    lines_changed_less_than(10),
                    single_file_modified(),
                    not(file_path_matches(["*.test.*"]))
                )
                output: WorkType.BugFix
            },
            Rule {
                name: "refactoring"
                condition: or(
                    file_renamed(),
                    net_lines_decreased(),
                    function_moved()
                )
                output: WorkType.Refactoring
            }
        ]
        
        // 작업 상태 추론 규칙
        work_status_rules: [
            Rule {
                name: "completed_work"
                condition: or(
                    todo_comments_removed(),
                    test_files_added(),
                    temporary_code_removed()
                )
                output: WorkStatus.Completed
            },
            Rule {
                name: "work_in_progress"
                condition: or(
                    todo_comments_added(),
                    stub_implementations_exist(),
                    incomplete_tests()
                )
                output: WorkStatus.InProgress
            },
            Rule {
                name: "planned_work"
                condition: or(
                    interface_only_defined(),
                    empty_function_bodies(),
                    scaffolding_code()
                )
                output: WorkStatus.Planned
            }
        ]
        
        // 코드 컨텍스트 추론 규칙
        code_context_rules: [
            Rule {
                name: "api_development"
                condition: code_contains_patterns([
                    "@Get", "@Post", "@Put", "@Delete",
                    "app.get", "app.post", "router", "endpoint"
                ])
                output: CodeContext.API
            },
            Rule {
                name: "database_work"
                condition: code_contains_patterns([
                    "CREATE TABLE", "ALTER TABLE", "SELECT", "INSERT",
                    "migration", "schema", "model"
                ])
                output: CodeContext.Database
            },
            Rule {
                name: "ui_development" 
                condition: code_contains_patterns([
                    "useState", "useEffect", "render", "component",
                    "<div", "className", "styled"
                ])
                output: CodeContext.UI
            }
        ]
    }
    
    // 함수 합성 패턴
    function_composition: {
        // 파이프라인 함수 (>>=)
        pipeline: "a -> (a -> b) -> b"
        
        // 맵 함수
        map: "(a -> b) -> List<a> -> List<b>"
        
        // 필터 함수  
        filter: "(a -> Boolean) -> List<a> -> List<a>"
        
        // 리듀스 함수
        reduce: "(a -> b -> a) -> a -> List<b> -> a"
        
        // 조건부 함수
        maybe: "(a -> Boolean) -> (a -> b) -> a -> Maybe<b>"
        
        // 함수 조합 예시
        analyze_work_types: compose(
            map(apply_work_type_rules),
            filter(is_valid_file_change),
            group_by(extract_work_type),
            reduce(aggregate_work_counts)
        )
    }
    
    // 불변 데이터 구조
    immutable_data_structures: {
        // 기본 분석 데이터
        AnalysisData: {
            repository: RepositoryInfo
            commits: ImmutableList<CommitData>
            diffs: ImmutableList<DiffData>
            file_changes: ImmutableList<FileChange>
            work_types: ImmutableSet<WorkType>
            metrics: ImmutableMap<String, Number>
            timestamp: Instant
            
            // 불변 업데이트 메서드
            with_metrics(new_metrics: Map<String, Number>): AnalysisData
            with_work_types(work_types: Set<WorkType>): AnalysisData
            add_file_change(change: FileChange): AnalysisData
        }
        
        // 파일 변경 정보
        FileChange: {
            path: FilePath
            lines_added: PositiveInt
            lines_deleted: PositiveInt
            change_type: ChangeType  // Added | Modified | Deleted | Renamed
            content_before: Optional<String>
            content_after: Optional<String>
            
            // 계산된 속성 (순수 함수)
            net_lines(): Int = lines_added - lines_deleted
            is_small_change(): Boolean = (lines_added + lines_deleted) < 10
            is_binary_file(): Boolean = path.extension in binary_extensions
        }
        
        // 작업 유형 정의
        WorkType: {
            Testing | Documentation | Configuration |
            FeatureDevelopment | BugFix | Refactoring |
            DependencyUpdate | Performance | Security
        }
        
        // 작업 상태 정의  
        WorkStatus: {
            Completed | InProgress | Planned | Blocked
        }
        
        // 코드 컨텍스트
        CodeContext: {
            API | Database | UI | Business | Infrastructure |
            Testing | Documentation | Configuration
        }
        
        // 분석 결과
        AnalysisResult: {
            summary: WorkSummary
            metrics: DevelopmentMetrics
            work_distribution: Map<WorkType, Count>
            status_distribution: Map<WorkStatus, Count>
            hotspots: List<FileHotspot>
            recommendations: List<Recommendation>
            
            // 결과 조합 (모노이드)
            combine(other: AnalysisResult): AnalysisResult
        }
        
        // 에러 타입
        AnalysisError: {
            ValidationError(message: String) |
            GitHubAPIError(status: Int, message: String) |
            RateLimitError(retry_after: Duration) |
            NetworkError(cause: Exception) |
            ParseError(file: String, line: Int)
        }
    }
    
    service WorkSummaryAnalyzer {
        description: "커밋 데이터를 구조화하여 Claude Code가 인사이트를 생성할 수 있도록 준비"
        
        functions: [
            extractWorkPatterns(commits: List<CommitData>) -> WorkPatterns,
            categorizeWorkStatus(commits: List<CommitData>) -> WorkStatusReport,
            calculateDevelopmentMetrics(commits: List<CommitData>) -> DevelopmentMetrics,
            prepareInsightData(commits: List<CommitData>, code_changes: CodeAnalysis) -> StructuredInsightData
        ]
        
        work_pattern_extraction: {
            current_focus: {
                description: "현재 집중하고 있는 작업 패턴 추출 (코드 기반)",
                data_points: [
                    "most_modified_files",
                    "file_change_clusters",     // 함께 변경되는 파일들
                    "code_hotspots",            // 자주 수정되는 코드 영역
                    "recent_file_patterns",     // 최근 파일 변경 패턴
                    "function_modifications"    // 함수/메서드 변경 추적
                ]
            }
            
            work_status_detection: {
                completed: {
                    code_indicators: [
                        "테스트 파일 추가 완료",
                        "TODO 주석 제거",
                        "임시 코드 제거",
                        "완성된 구현 패턴"
                    ]
                },
                in_progress: {
                    code_indicators: [
                        "TODO/FIXME 주석 증가",
                        "스텁 구현 존재",
                        "테스트 미완성",
                        "임시 변수/함수 사용"
                    ]
                },
                planned: {
                    code_indicators: [
                        "인터페이스만 정의",
                        "빈 함수 본문",
                        "스캐폴딩 코드",
                        "주석으로만 작성된 로직"
                    ]
                }
            }
            
            metrics_calculation: {
                velocity: {
                    commits_per_day: "일별 커밋 수",
                    lines_per_day: "일별 코드 변경량",
                    files_per_commit: "커밋당 평균 파일 수"
                },
                patterns: {
                    commit_time_distribution: "시간대별 커밋 분포",
                    work_session_duration: "작업 세션 길이",
                    break_patterns: "휴식 패턴"
                },
                quality: {
                    fix_rate: "버그 수정 비율",
                    refactor_rate: "리팩토링 비율",
                    test_coverage_trend: "테스트 커버리지 추세"
                }
            }
        }
        
        output_structure: {
            structured_data: {
                description: "Claude Code가 분석할 수 있는 구조화된 데이터",
                format: "JSON with semantic categorization",
                includes: [
                    "raw_commit_data",
                    "extracted_patterns",
                    "calculated_metrics",
                    "code_change_summary"
                ]
            },
            
            metadata: {
                analysis_timestamp: "분석 시점",
                data_completeness: "데이터 완전성 지표",
                confidence_scores: "패턴 신뢰도 점수"
            }
        }
        
        note: "이 서비스는 데이터를 구조화만 하고, 실제 인사이트 생성은 Claude Code가 수행합니다"
    }
}
```

## 5. 응답 포맷팅

```dsl
module ResponseFormatting {
    
    formatter MarkdownReportFormatter {
        
        function formatCommitAnalysis(analysis: CommitAnalysisResult) -> MarkdownContent {
            template: """
# 📊 {owner}/{repo} 커밋 분석 결과 (최근 {days}일)

## 📈 전체 통계
- **총 커밋 수**: {total_commits}개
- **참여 개발자**: {unique_authors}명
- **가장 활발한 시간**: {most_active_hour}시
- **가장 활발한 요일**: {most_active_day}

## 👥 주요 기여자
{top_authors_list}

## 🔍 코드 작업 유형 분석
- **기능 개발**: {feature_development_count}개
- **버그 수정**: {bug_fix_count}개  
- **테스트 작성**: {test_work_count}개
- **리팩토링**: {refactoring_count}개
- **설정/환경**: {configuration_count}개
- **문서화**: {documentation_count}개

## 📝 주요 변경 파일
{top_changed_files_list}
"""
        }
        
        function formatDiffContent(diff: DiffContent, sha: String) -> MarkdownContent {
            size_threshold: 5000_characters
            
            if diff.size > size_threshold:
                return formatDiffSummary(diff, sha)
            else:
                return formatFullDiff(diff, sha)
        }
        
        function formatRepositorySummary(repo: RepositoryData, activity: ActivityData) -> MarkdownContent {
            template: """
# 📁 {owner}/{repo} 리포지토리 요약

## ℹ️ 기본 정보
- **설명**: {description}
- **언어**: {primary_language}
- **Stars**: {stars_count:,}개 ⭐
- **Forks**: {forks_count:,}개 🍴
- **생성일**: {created_at}
- **최종 업데이트**: {updated_at}

## 📊 최근 7일간 활동
- **커밋**: {recent_commits}개
- **활발한 개발자**: {active_developers}명
- **주요 작업**: {primary_work_type}

## 🔗 링크
- GitHub: {html_url}
- Clone: `git clone {clone_url}`
"""
        }
        
        function formatCodeAnalysis(analysis: CodeAnalysisResult) -> MarkdownContent {
            template: """
# 🔬 {owner}/{repo} 코드 변경 분석 (최근 {days}일)

## 📊 파일별 변경 통계
- **총 변경 파일**: {total_files_changed}개
- **추가된 라인**: +{lines_added:,}
- **삭제된 라인**: -{lines_deleted:,}
- **코드 변경률**: {churn_rate:.1%}

### 가장 많이 변경된 파일 Top 5
{top_changed_files_list}

## 📈 코드 복잡도 변화
- **순환 복잡도**: {cyclomatic_change:+.1f}
- **인지 복잡도**: {cognitive_change:+.1f}
- **평균 메서드 길이**: {method_length_change:+.1f} 라인

## 🏗️ 주요 구조 변경
### 새로 추가된 기능
{new_functions_list}

### 수정된 주요 함수/클래스
{modified_structures_list}

## 📦 의존성 변경
- **새로 추가**: {new_dependencies_list}
- **제거됨**: {removed_dependencies_list}
- **업데이트**: {updated_dependencies_list}

## 💼 작업 유형 분석
{work_type_distribution_chart}
"""
        }
        
        function formatWorkSummary(summary: WorkSummaryReport) -> MarkdownContent {
            template: """
# 💡 {owner}/{repo} 작업 내용 인사이트

## 🎯 현재 집중 작업
{current_focus_list}

## ✅ 최근 완료된 작업
{completed_work_list}

## 🔄 진행 중인 작업
{work_in_progress_list}

## 🔮 예상 다음 단계
{next_steps_list}

## 📈 개발 속도 메트릭
- **일일 평균 커밋**: {daily_commits:.1f}개
- **주간 코드 변경량**: {weekly_code_change:,} 라인
- **기능 완성 속도**: {feature_velocity:.1f} 기능/주
- **버그 수정 속도**: {bug_fix_rate:.1f} 이슈/일

## 👥 협업 인사이트
{collaboration_insights}

## 📝 전체 요약
{overall_summary}
"""
        }
    }
}
```

## 6. 함수형 에러 처리 및 로깅

```dsl
module FunctionalErrorHandling {
    
    // Result 타입 (Either 모나드)
    type Result<T, E> = Success<T> | Failure<E>
    
    // 함수형 에러 처리 전략
    error_handling_patterns: {
        
        // 모나딕 체이닝
        monadic_pipeline: {
            description: "Result 타입으로 에러 전파 없이 파이프라인 처리"
            pattern: """
                validateInput(params)
                  .flatMap(fetchGitHubData)
                  .flatMap(analyzeCommits) 
                  .flatMap(formatReport)
                  .fold(
                    onSuccess = return_success,
                    onFailure = handle_error
                  )
            """
        }
        
        // 에러 복구 패턴
        error_recovery: {
            retry_with_backoff: "Result<T> -> (RetryConfig -> Result<T>)"
            fallback_value: "Result<T> -> T -> T"
            alternative_source: "Result<T> -> (() -> Result<T>) -> Result<T>"
        }
        
        // 에러 변환
        error_transformation: {
            map_error: "(E1 -> E2) -> Result<T, E1> -> Result<T, E2>"
            recover: "(E -> Result<T, E>) -> Result<T, E> -> Result<T, E>"
            ensure: "(T -> Boolean, E) -> Result<T, E> -> Result<T, E>"
        }
    }
    
    // 구체적 에러 처리 함수
    error_handlers: {
        
        handle_github_api_error: {
            signature: "GitHubAPIError -> Result<RetryAction, UserError>"
            implementation: """
                match error:
                  case RateLimitExceeded(retry_after) -> 
                    Success(WaitAndRetry(exponential_backoff(retry_after)))
                  case RepositoryNotFound(repo) -> 
                    Failure(UserError("리포지토리 '{repo}'를 찾을 수 없습니다"))
                  case Unauthorized -> 
                    Failure(UserError("GitHub 토큰을 확인해주세요"))
                  case NetworkError(cause) -> 
                    Success(RetryWithTimeout(increased_timeout()))
            """
        }
        
        handle_validation_error: {
            signature: "ValidationError -> Result<Never, UserError>"
            implementation: """
                match error:
                  case InvalidRepoName(name) -> 
                    Failure(UserError("올바른 형식: owner/repo-name"))
                  case InvalidCommitSHA(sha) -> 
                    Failure(UserError("커밋 SHA는 7-40자리 16진수"))
                  case InvalidDateRange(days) -> 
                    Failure(UserError("날짜 범위: 1-30일"))
            """
        }
        
        handle_analysis_error: {
            signature: "AnalysisError -> Result<PartialResult, UserError>"
            implementation: """
                match error:
                  case ParseError(file, line) -> 
                    Success(PartialResult.with_skipped_file(file))
                  case UnsupportedLanguage(lang) -> 
                    Success(PartialResult.with_basic_analysis())
                  case ComplexityTimeout -> 
                    Success(PartialResult.with_simplified_metrics())
            """
        }
    }
    
    // 함수형 로깅 (부작용 격리)
    functional_logging: {
        
        // 로그 데이터 (불변)
        LogEntry: {
            timestamp: Instant
            level: LogLevel  // Debug | Info | Warn | Error
            event: LogEvent
            context: Map<String, String>
            correlation_id: UUID
        }
        
        // 로그 이벤트 타입
        LogEvent: {
            AnalysisStarted(repo: RepoIdentifier) |
            APIRequestSent(endpoint: String, params: Map<String, String>) |
            APIResponseReceived(status: Int, duration: Duration) |
            ErrorOccurred(error: AnalysisError, recovery_attempted: Boolean) |
            AnalysisCompleted(duration: Duration, result_size: Int)
        }
        
        // 로깅 함수 (Reader 모나드)
        logging_functions: {
            log_analysis_step: "LogLevel -> String -> ReaderT<LogConfig, IO, Unit>"
            log_with_context: "Map<String, String> -> LogEvent -> ReaderT<LogConfig, IO, Unit>"
            structured_log: "LogEntry -> ReaderT<LogConfig, IO, Unit>"
        }
        
        // 로그 설정
        LogConfig: {
            level: LogLevel
            format: "structured_json" | "human_readable"
            destinations: List<LogDestination>  // Console | File | Remote
            sensitive_field_mask: Set<String>
            correlation_tracking: Boolean
        }
    }
    
    // 모니터링 및 메트릭 (함수형)
    functional_monitoring: {
        
        // 메트릭 타입 (불변)
        Metric: {
            Counter(name: String, value: Long, tags: Map<String, String>) |
            Gauge(name: String, value: Double, tags: Map<String, String>) |
            Timer(name: String, duration: Duration, tags: Map<String, String>) |
            Histogram(name: String, values: List<Double>, tags: Map<String, String>)
        }
        
        // 메트릭 수집 함수
        metric_collectors: {
            time_operation: "String -> IO<A> -> ReaderT<MetricConfig, IO, (A, Timer)>"
            count_event: "String -> Map<String, String> -> ReaderT<MetricConfig, IO, Unit>"
            measure_pipeline_performance: "Pipeline<A, B> -> A -> ReaderT<MetricConfig, IO, (B, List<Metric>)>"
        }
        
        // 건강 상태 체크 (순수)
        health_checks: {
            check_github_connectivity: "() -> IO<Result<HealthStatus, ConnectivityError>>"
            check_rate_limits: "GitHubClient -> IO<Result<RateLimitStatus, APIError>>"
            check_memory_usage: "() -> IO<MemoryStatus>"
            aggregate_health: "List<HealthCheck> -> OverallHealth"
        }
    }
}
```

## 7. 설정 및 환경 관리

```dsl
module Configuration {
    
    environment EnvironmentSetup {
        required_variables: {
            GITHUB_TOKEN: {
                description: "GitHub Personal Access Token"
                validation: "^ghp_[a-zA-Z0-9]{36}$"
                security: high
            }
        }
        
        optional_variables: {
            OPENROUTER_API_KEY: {
                description: "OpenRouter API Key for AI insights"
                validation: "^sk-or-v1-.*"
                default: null
            }
            
            LOG_LEVEL: {
                description: "Logging level"
                options: ["DEBUG", "INFO", "WARNING", "ERROR"]
                default: "INFO"
            }
            
            MAX_COMMITS_PER_REQUEST: {
                description: "Maximum commits to analyze per request"
                type: integer
                minimum: 10
                maximum: 100
                default: 100
            }
        }
    }
    
    claude_code_config ClaudeCodeIntegration {
        config_file_location: {
            macos: "~/Library/Application Support/Claude/claude_desktop_config.json"
            windows: "%APPDATA%\\Claude\\claude_desktop_config.json"
            linux: "~/.config/claude/claude_desktop_config.json"
        }
        
        mcp_server_entry: {
            name: "github-commit-analyzer"
            command: "python"
            args: ["/absolute/path/to/server.py"]
            env: {
                GITHUB_TOKEN: "${GITHUB_TOKEN}"
                OPENROUTER_API_KEY: "${OPENROUTER_API_KEY}"
            }
        }
        
        alternative_uv_config: {
            command: "uv"
            args: [
                "run",
                "--directory", "/absolute/path/to/project",
                "python", "server.py"
            ]
        }
    }
}
```

## 8. 버티컬 프로젝트 구조

```dsl
project_structure VerticalArchitecture {
    paradigm: "Feature-based vertical slicing"
    organization: "domain_driven_modules"
    
    root_structure: {
        src/
        ├── core/                    # 핵심 도메인 로직 (순수 함수)
        │   ├── domain/             # 도메인 모델과 타입 정의
        │   │   ├── types.py        # 불변 데이터 타입들
        │   │   ├── errors.py       # 에러 타입 정의
        │   │   └── rules.py        # 비즈니스 규칙
        │   ├── analysis/           # 분석 로직 (순수 함수들)
        │   │   ├── work_type_inference.py
        │   │   ├── metrics_calculation.py
        │   │   ├── pattern_detection.py
        │   │   └── data_transformation.py
        │   └── utils/              # 유틸리티 함수들
        │       ├── functional.py   # 함수형 프로그래밍 유틸
        │       ├── validation.py   # 입력 검증 함수들
        │       └── formatting.py   # 출력 포맷팅 함수들
        │
        ├── features/               # MCP 도구별 버티컬 슬라이스
        │   ├── analyze_commits/    # analyze_commits 도구의 모든 것
        │   │   ├── __init__.py
        │   │   ├── handler.py      # MCP 핸들러 (I/O 경계)
        │   │   ├── pipeline.py     # 분석 파이프라인 조합
        │   │   ├── rules.py        # 이 기능 특화 규칙들
        │   │   └── formatters.py   # 출력 포맷터
        │   │
        │   ├── analyze_code_changes/
        │   │   ├── __init__.py
        │   │   ├── handler.py
        │   │   ├── pipeline.py
        │   │   ├── complexity_analysis.py
        │   │   ├── structural_analysis.py
        │   │   └── formatters.py
        │   │
        │   ├── get_commit_diff/
        │   │   ├── __init__.py
        │   │   ├── handler.py
        │   │   ├── pipeline.py
        │   │   ├── diff_parser.py
        │   │   └── formatters.py
        │   │
        │   └── repository_summary/
        │       ├── __init__.py
        │       ├── handler.py
        │       ├── pipeline.py
        │       ├── activity_analyzer.py
        │       └── formatters.py
        │
        ├── infrastructure/         # 외부 시스템 연동 (부작용 격리)
        │   ├── github/            # GitHub API 클라이언트
        │   │   ├── __init__.py
        │   │   ├── client.py      # HTTP 클라이언트
        │   │   ├── auth.py        # 인증 처리
        │   │   ├── rate_limiter.py # 요청 제한 처리
        │   │   └── models.py      # API 응답 모델
        │   │
        │   ├── mcp/               # MCP 프로토콜 처리
        │   │   ├── __init__.py
        │   │   ├── server.py      # MCP 서버 구현
        │   │   ├── protocol.py    # 프로토콜 핸들링
        │   │   └── tools.py       # 도구 등록 및 라우팅
        │   │
        │   ├── logging/           # 로깅 시스템
        │   │   ├── __init__.py
        │   │   ├── structured.py  # 구조화된 로깅
        │   │   ├── correlation.py # 상관관계 추적
        │   │   └── formatters.py  # 로그 포맷터
        │   │
        │   └── monitoring/        # 메트릭 및 모니터링
        │       ├── __init__.py
        │       ├── metrics.py     # 메트릭 수집
        │       ├── health.py      # 건강 상태 체크
        │       └── performance.py # 성능 측정
        │
        ├── config/                # 설정 관리
        │   ├── __init__.py
        │   ├── settings.py        # 환경별 설정
        │   ├── validation.py      # 설정 검증
        │   └── constants.py       # 상수 정의
        │
        └── main.py               # 애플리케이션 진입점
    }
    
    vertical_slice_pattern: {
        description: "각 기능이 독립적인 수직 슬라이스를 형성"
        
        feature_structure: {
            handler: "MCP 도구 인터페이스 (I/O 경계)"
            pipeline: "순수 함수들의 조합으로 비즈니스 로직 구현"
            rules: "해당 기능 특화 규칙과 정책"
            formatters: "출력 형식 변환 (순수 함수)"
        }
        
        dependencies: {
            inward: "feature → core (의존성 역전)"
            outward: "feature → infrastructure (추상화 통해)"
            horizontal: "feature간 직접 의존성 금지"
        }
        
        benefits: [
            "기능별 독립적 개발 및 테스트",
            "명확한 책임 분리",
            "수평 확장성 (새 도구 추가 용이)",
            "함수형 파이프라인의 명확한 구조화"
        ]
    }
    
    functional_organization: {
        pure_functions: {
            location: "core/ + features/*/pipeline.py"
            characteristics: [
                "부작용 없음",
                "테스트 용이성",
                "조합 가능성",
                "병렬 처리 안전성"
            ]
        }
        
        side_effects: {
            location: "infrastructure/ + features/*/handler.py"
            characteristics: [
                "I/O 경계로 격리",
                "의존성 주입으로 테스트 가능",
                "에러 처리 전용 영역"
            ]
        }
        
        composition_rules: {
            "handler → pipeline → core": "의존성 방향"
            "pure_function ∘ pure_function": "함수 조합"
            "IO<Result<T, E>>": "부작용 + 에러 처리 타입"
        }
    }
}
```

```dsl
detailed_file_organization FileStructure {
    
    // 핵심 도메인 (순수 함수 영역)
    core_domain: {
        "src/core/domain/types.py": {
            purpose: "불변 데이터 타입과 도메인 모델"
            content: [
                "AnalysisData", "FileChange", "WorkType", 
                "WorkStatus", "CodeContext", "AnalysisResult"
            ]
            pattern: "dataclass(frozen=True) + 계산된 속성"
        }
        
        "src/core/domain/errors.py": {
            purpose: "에러 타입 계층구조"
            content: [
                "AnalysisError", "ValidationError", "GitHubAPIError",
                "RateLimitError", "NetworkError", "ParseError"
            ]
            pattern: "Union types for functional error handling"
        }
        
        "src/core/domain/rules.py": {
            purpose: "비즈니스 규칙과 정책"
            content: [
                "WorkTypeRules", "WorkStatusRules", "CodeContextRules"
            ]
            pattern: "Rule = Callable[[T], bool] + output mapping"
        }
    }
    
    // 분석 로직 (순수 함수들)
    core_analysis: {
        "src/core/analysis/work_type_inference.py": {
            functions: [
                "infer_from_file_patterns: List[FileChange] -> List[WorkType]",
                "infer_from_code_content: CodeContent -> List[WorkType]", 
                "apply_work_type_rules: List[Rule] -> FileChange -> WorkType"
            ]
        }
        
        "src/core/analysis/metrics_calculation.py": {
            functions: [
                "calculate_velocity: List[Commit] -> VelocityMetrics",
                "calculate_complexity: CodeChange -> ComplexityMetrics",
                "calculate_patterns: List[Commit] -> TimePatterns"
            ]
        }
        
        "src/core/analysis/pattern_detection.py": {
            functions: [
                "detect_hotspots: List[FileChange] -> List[Hotspot]",
                "detect_clusters: List[FileChange] -> List[Cluster]",
                "detect_trends: List[Metric] -> List[Trend]"
            ]
        }
        
        "src/core/analysis/data_transformation.py": {
            functions: [
                "extract_diffs: GitHubResponse -> List[DiffData]",
                "parse_commits: RawCommitData -> List[CommitData]",
                "normalize_file_paths: List[str] -> List[FilePath]"
            ]
        }
    }
    
    // 기능별 버티컬 슬라이스
    feature_slices: {
        "src/features/analyze_commits/": {
            "handler.py": {
                purpose: "MCP 도구 진입점 (I/O 경계)"
                pattern: """
                async def handle_analyze_commits(params: AnalyzeCommitsParams) -> Result[Report, Error]:
                    return await (
                        validate_params(params)
                        .and_then_async(fetch_github_data)
                        .and_then(run_analysis_pipeline)
                        .map(format_commit_analysis)
                    )
                """
            }
            
            "pipeline.py": {
                purpose: "순수 함수들의 조합"
                pattern: """
                def analysis_pipeline(github_data: GitHubData) -> AnalysisResult:
                    return pipe(
                        github_data,
                        extract_commit_patterns,
                        infer_work_types,
                        calculate_metrics,
                        aggregate_results
                    )
                """
            }
            
            "rules.py": {
                purpose: "커밋 분석 특화 규칙"
                content: "commit_patterns, author_analysis_rules, time_pattern_rules"
            }
            
            "formatters.py": {
                purpose: "Markdown 리포트 생성 (순수 함수)"
                functions: [
                    "format_commit_analysis: AnalysisResult -> MarkdownReport",
                    "format_author_stats: AuthorStats -> str",
                    "format_time_patterns: TimePatterns -> str"
                ]
            }
        }
        
        "src/features/analyze_code_changes/": {
            structure: "handler.py + pipeline.py + rules.py + formatters.py"
            specialization: [
                "complexity_analysis.py: 복잡도 메트릭 계산",
                "structural_analysis.py: 코드 구조 변화 분석"
            ]
        }
        
        "src/features/get_commit_diff/": {
            structure: "handler.py + pipeline.py + rules.py + formatters.py"
            specialization: [
                "diff_parser.py: Git diff 파싱 및 분석"
            ]
        }
        
        "src/features/repository_summary/": {
            structure: "handler.py + pipeline.py + rules.py + formatters.py"
            specialization: [
                "activity_analyzer.py: 저장소 활동 패턴 분석"
            ]
        }
    }
    
    // 인프라스트럭처 (부작용 격리)
    infrastructure: {
        "src/infrastructure/github/client.py": {
            purpose: "GitHub API HTTP 클라이언트"
            pattern: "async def get_commits(repo: str) -> IO[Result[List[Commit], APIError]]"
        }
        
        "src/infrastructure/mcp/server.py": {
            purpose: "MCP 서버 구현"
            pattern: "도구 등록 및 라우팅, JSON-RPC 처리"
        }
        
        "src/infrastructure/logging/structured.py": {
            purpose: "구조화된 로깅"
            pattern: "ReaderT[LogConfig, IO, Unit] 모나드 기반"
        }
    }
    
    // 설정 및 진입점
    application_layer: {
        "src/config/settings.py": {
            purpose: "환경 설정 관리"
            pattern: "불변 설정 객체 + 검증 함수"
        }
        
        "src/main.py": {
            purpose: "애플리케이션 진입점"
            pattern: """
            def main():
                config = load_config()
                server = create_mcp_server(config)
                register_tools(server)
                run_server(server)
            """
        }
    }
}
```

## 9. 함수형 개발 워크플로우

```dsl
workflow FunctionalDevelopmentWorkflow {
    
    phase Setup {
        approach: "순수 함수 우선, 부작용 격리"
        
        functional_setup_pipeline: [
            validate_environment_config,
            create_immutable_config,
            initialize_pure_functions,
            setup_io_boundary_layer,
            verify_pipeline_composition
        ]
        
        validation_functions: {
            verify_github_token: "Config -> Result<ValidConfig, ConfigError>"
            test_mcp_handshake: "MCPConfig -> IO<Result<HandshakeSuccess, MCPError>>"
            validate_function_composition: "Pipeline -> Result<ValidPipeline, CompositionError>"
        }
    }
    
    phase FunctionalDevelopment {
        principles: [
            "순수 함수부터 구현",
            "부작용을 경계로 밀어내기",
            "타입으로 불변성 보장",
            "속성 기반 테스트 활용"
        ]
        
        development_pipeline: {
            step1_pure_logic: {
                description: "비즈니스 로직을 순수 함수로 구현"
                testing: "속성 기반 테스트 (Property-based testing)"
                tools: ["QuickCheck", "Hypothesis", "fast-check"]
            }
            
            step2_composition: {
                description: "작은 함수들을 파이프라인으로 조합"
                testing: "파이프라인 단위 테스트"
                validation: "타입 체크 및 조합 규칙 검증"
            }
            
            step3_io_integration: {
                description: "I/O 경계에서 순수 함수 연결"
                testing: "모의 객체를 이용한 통합 테스트"
                monitoring: "부작용 실행 메트릭"
            }
        }
        
        testing_strategy: {
            property_based_tests: {
                description: "순수 함수의 속성 검증"
                examples: [
                    "forall files: analyze_work_type(file).is_valid_work_type()",
                    "forall commits: extract_metrics(commits).sum >= 0",
                    "forall rules, file: apply_rules(rules, file).length <= rules.length"
                ]
            }
            
            pipeline_tests: {
                description: "함수 조합의 동작 검증"
                approach: "입력-출력 쌍 테스트 + 중간 단계 검증"
            }
            
            integration_tests: {
                description: "I/O 경계 테스트"
                approach: "의존성 주입으로 실제 GitHub API 모의"
            }
        }
        
        debugging_techniques: {
            pipeline_tracing: {
                description: "각 파이프라인 단계의 입력/출력 추적"
                implementation: "Reader 모나드로 디버그 컨텍스트 전달"
            }
            
            pure_function_isolation: {
                description: "순수 함수는 REPL에서 직접 테스트"
                benefit: "빠른 피드백 루프"
            }
            
            property_shrinking: {
                description: "실패한 속성 테스트의 최소 반례 찾기"
                tools: "QuickCheck shrinking"
            }
        }
    }
    
    phase FunctionalDeployment {
        immutable_deployment: {
            description: "불변 배포 아티팩트"
            approach: "함수형 설정 + 순수 함수 번들"
        }
        
        monitoring_pipeline: {
            metrics_collection: "순수 함수로 메트릭 계산"
            health_monitoring: "함수형 건강 상태 체크"
            error_aggregation: "Result 타입 기반 에러 수집"
        }
        
        performance_optimization: {
            memoization: "순수 함수 결과 캐싱"
            lazy_evaluation: "필요시에만 계산"
            parallel_processing: "독립적 분석 작업 병렬화"
        }
    }
}
```

## 9. 사용자 인터페이스 (Claude Code)

```dsl
interface ClaudeCodeInteraction {
    
    natural_language_commands: [
        "GitHub 리포지토리 분석",
        "커밋 패턴 확인",
        "특정 커밋 상세 조회",
        "프로젝트 활동 요약"
    ]
    
    example_conversations: {
        code_analysis: {
            user: "facebook/react 리포지토리의 최근 작업 내용을 분석해줘"
            system: "analyze_code_changes 도구 호출"
            response: "코드 변경 기반 작업 분석 리포트"
        }
        
        work_investigation: {
            user: "어떤 기능을 개발하고 있는지 코드로 파악해줘"
            system: "analyze_code_changes + get_commit_diff 도구 조합"
            response: "코드 분석 기반 작업 내용"
        }
        
        progress_tracking: {
            user: "현재 진행 중인 작업이 무엇인지 알려줘"
            system: "코드의 TODO/FIXME, 스텁 구현 등 분석"
            response: "진행 중 작업 목록과 완성도"
        }
    }
    
    error_scenarios: {
        invalid_repository: {
            user: "존재하지않는repo 분석해줘"
            response: "리포지토리를 찾을 수 없다는 명확한 안내"
        }
        
        rate_limit: {
            user: "너무 많은 분석 요청"
            response: "API 제한 상황 설명 및 대기 안내"
        }
    }
}
```

---