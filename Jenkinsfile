pipeline {
  agent any

  environment {
    REGISTRY = 'docker.io/yuripbong3'       // Replace with your Docker Hub / registry
    IMAGE_NAME = 'team-a-backend'                // Your image/project name
    IMAGE_TAG = "v0.${env.BUILD_NUMBER}"
    FULL_IMAGE = "${env.REGISTRY}/${env.IMAGE_NAME}:${env.IMAGE_TAG}"
  }

  options {
    timestamps()
    skipStagesAfterUnstable()
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build & Push Image') {
      steps {
        script {
          sh """
            docker build -t ${FULL_IMAGE} .
            docker push ${FULL_IMAGE}
          """
        }
      }
    }

//     stage('Trigger CD Pipeline') {
//       steps {
//         script {
//           build job: 'deploy-cd',
//             parameters: [
//               string(name: 'IMAGE_TAG', value: "${IMAGE_TAG}"),
//               booleanParam(name: 'REQUIRE_APPROVAL', value: false)
//             ],
//             wait: false
//         }
//       }
//     }
   }

  post {
    success {
      echo "CI pipeline succeeded. Image: ${FULL_IMAGE}"
      // Optional: Slack Notification
      slackSend channel: '#ci-notify', message: "✅ CI passed: ${FULL_IMAGE}"
    }

    failure {
      echo "CI pipeline failed."
      // Optional: Slack Notification
      slackSend channel: '#ci-notify', message: "❌ CI failed: ${env.BUILD_URL}"
    }
  }
}