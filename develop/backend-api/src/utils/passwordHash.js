const bcrypt = require('bcrypt');

function isValidBcryptHash(passwordHash) {
  return (
    typeof passwordHash === 'string' &&
    /^\$2[aby]\$(0[4-9]|[12][0-9]|3[01])\$[./A-Za-z0-9]{53}$/.test(passwordHash)
  );
}

async function verifyPassword(password, passwordHash) {
  if (!isValidBcryptHash(passwordHash)) {
    return false;
  }

  try {
    return await bcrypt.compare(password, passwordHash);
  } catch (error) {
    return false;
  }
}

module.exports = {
  isValidBcryptHash,
  verifyPassword,
};
