const { PrismaClient } = require('@prisma/client');

// 인스턴스를 하나만 생성하여 애플리케이션 전체에서 재사용합니다.
const prisma = new PrismaClient();

module.exports = prisma;
