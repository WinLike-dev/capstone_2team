FROM node:24-alpine

# 앱 디렉터리 생성 및 설정
WORKDIR /usr/src/app

# 앱 의존성 설치
# package.json과 package-lock.json 복사
COPY package*.json ./

# 프로덕션 의존성만 설치
RUN npm ci --only=production

# 앱 소스 추가
COPY . .

# 포트 매핑
EXPOSE 8080

# 서버 실행
CMD [ "npm", "start" ]
