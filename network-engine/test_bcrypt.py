import bcrypt

password = b'admin'
hash = b'$2b$12$KSRX8/vB.nNvfdZJ0L94veaTilDIsJRA7Gwk5ApMzxfgT8gNpoUyu'
result = bcrypt.checkpw(password, hash)
print('admin/admin:', result)

# Test with a known bcrypt hash of "admin"
test_hash = bcrypt.hashpw(b'admin', bcrypt.gensalt())
print('Test hash of "admin":', test_hash)
print('Test check:', bcrypt.checkpw(b'admin', test_hash))