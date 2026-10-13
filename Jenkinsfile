pipeline {
    agent any

    environment {
        IMAGE    = 'demo-app'
        TAG      = "${env.BUILD_NUMBER}"
        NETWORK  = 'monitoring'
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Test') {
            steps {
                // Runs pytest inside the image build, so no host volume mounts are needed
                sh 'docker build --target test -t ${IMAGE}:test app/'
            }
        }

        stage('Build') {
            steps {
                sh 'docker build --target runtime -t ${IMAGE}:${TAG} -t ${IMAGE}:latest app/'
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                  docker rm -f ${IMAGE} || true
                  docker run -d --name ${IMAGE} \
                    --network ${NETWORK} \
                    -p 5000:5000 \
                    --restart unless-stopped \
                    ${IMAGE}:${TAG}
                '''
            }
        }

        stage('Smoke test') {
            steps {
                // Jenkins sits on the same Docker network, so it can reach the app by name
                retry(5) {
                    sleep 3
                    sh 'curl -fsS http://${IMAGE}:5000/health'
                }
            }
        }
    }

    post {
        success { echo "Deployed ${IMAGE}:${TAG} - check Grafana at http://localhost:3000" }
        failure { echo 'Pipeline failed - see stage logs above.' }
        always  { sh 'docker image prune -f || true' }
    }
}
