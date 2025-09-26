#!/bin/bash

# JSON Annotation Validator Docker 실행 스크립트

echo "🚀 JSON Annotation Validator Docker 시작..."

# Docker 이미지 빌드
echo "📦 Docker 이미지 빌드 중..."
docker-compose build

# 컨테이너 시작
echo "🐳 컨테이너 시작 중..."
docker-compose up -d

# 상태 확인
echo "✅ 컨테이너 상태 확인..."
docker-compose ps

echo ""
echo "🌐 애플리케이션이 다음 주소에서 실행 중입니다:"
echo "   - 직접 접속: http://localhost:5000"
echo "   - Nginx 프록시: http://localhost:80 (nginx 프로필 사용 시)"
echo ""
echo "📋 유용한 명령어:"
echo "   - 로그 확인: docker-compose logs -f"
echo "   - 컨테이너 중지: docker-compose down"
echo "   - Nginx와 함께 실행: docker-compose --profile nginx up -d"
echo ""
echo "🎉 설정 완료!"
