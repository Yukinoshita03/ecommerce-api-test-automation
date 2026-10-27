pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        choice(name: 'CODE_SOURCE', choices: ['LOCAL', 'GITHUB'],
               description: 'LOCAL 使用当前本机代码；GITHUB 拉取远端 main 已提交代码')
        choice(name: 'TEST_SCOPE', choices: ['UNIT_SMOKE', 'UNIT', 'API', 'ALL'],
               description: '先运行 UNIT_SMOKE；API 和 ALL 会访问测试服务并可能写入测试数据')
        string(name: 'TEST_BASE_URL', defaultValue: 'http://127.0.0.1:8000',
               description: 'API / UI 测试的服务地址')
    }

    environment {
        LOCAL_PROJECT = '/Users/tankaiwen/python/ecommerce-api-tests'
        PATH = "/Users/tankaiwen/.npm-global/bin:/opt/homebrew/bin:${env.PATH}"
    }

    stages {
        stage('选择代码') {
            steps {
                script {
                    // 新建任务第一次运行时参数可能尚未注入，先给出默认值。
                    env.SELECTED_SCOPE = params.TEST_SCOPE ?: 'UNIT_SMOKE'
                    env.TEST_BASE_URL = params.TEST_BASE_URL ?: 'http://127.0.0.1:8000'
                    if (params.CODE_SOURCE == 'GITHUB') {
                        // 仅对拉取代码重试，不自动重跑有写入副作用的测试。
                        retry(2) {
                            git branch: 'main', url: 'https://github.com/Yukinoshita03/ecommerce-api-test-automation.git'
                        }
                        env.TEST_PROJECT = env.WORKSPACE
                        echo '使用 GitHub main 已提交的代码。'
                    } else {
                        env.TEST_PROJECT = env.LOCAL_PROJECT
                        echo '使用本机工作区，包括尚未提交的改动。'
                    }
                }
            }
        }

        stage('安装依赖') {
            steps {
                sh '''
                    set -eu
                    python3 --version
                    python3 -m venv "$WORKSPACE/.ci-venv"
                    "$WORKSPACE/.ci-venv/bin/python" -m pip install \
                        --disable-pip-version-check -r "$TEST_PROJECT/requirements.txt"
                '''
            }
        }

        stage('执行 Pytest') {
            steps {
                sh '''
                    set -eu
                    mkdir -p "$WORKSPACE/reports"
                    cd "$TEST_PROJECT"

                    case "$SELECTED_SCOPE" in
                      UNIT_SMOKE)
                        if [ -d testcase/unit ]; then
                          set -- testcase/unit/test_config.py testcase/unit/test_timeout.py
                        else
                          set -- tests/test_config.py tests/test_timeout.py
                        fi
                        ;;
                      UNIT)
                        if [ ! -d testcase/unit ]; then
                          echo '当前 Git 版本尚没有 testcase/unit；请先提交本机改动。' >&2
                          exit 2
                        fi
                        set -- testcase/unit
                        ;;
                      API)
                        if [ ! -d testcase/api ]; then
                          echo '当前 Git 版本尚没有 testcase/api；请先提交本机改动。' >&2
                          exit 2
                        fi
                        set -- testcase/api
                        ;;
                      ALL)
                        if [ ! -d testcase ]; then
                          echo '当前 Git 版本尚没有 testcase；请先提交本机改动。' >&2
                          exit 2
                        fi
                        set -- testcase
                        ;;
                      *) echo "未知的测试范围: $SELECTED_SCOPE" >&2; exit 2 ;;
                    esac

                    "$WORKSPACE/.ci-venv/bin/python" -m pytest "$@" \
                        --junitxml="$WORKSPACE/reports/junit.xml" \
                        --alluredir="$WORKSPACE/reports/allure-results" \
                        --clean-alluredir
                '''
            }
        }
    }

    post {
        always {
            script {
                if (fileExists('reports/junit.xml')) {
                    junit 'reports/junit.xml'
                }
                if (fileExists('reports/allure-results')) {
                    allure allureVersion: '3', includeProperties: false,
                           results: [[path: 'reports/allure-results']]
                }
                archiveArtifacts artifacts: 'reports/junit.xml,reports/allure-results/**',
                                 allowEmptyArchive: true
            }
        }
        cleanup {
            cleanWs deleteDirs: true, disableDeferredWipeout: true
        }
    }
}
