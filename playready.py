# -*- coding: utf-8 -*-

from Crypto.Cipher import AES
import hashlib
import base64
import uuid
import sys

CONTENT_KEY_SEED="00000000000000111111111111111111"

class PlayReadyLib:

  # コンテンツキーの生成
  # https://docs.microsoft.com/en-us/playready/specifications/playready-key-seed
  def gen_content_key(self, key_id):
    key_id = uuid.UUID(key_id).bytes_le

    seed_bytes = b""
    for x in range(len(CONTENT_KEY_SEED)):
      if x % 2 == 1:
          continue
      if x + 2 > len(CONTENT_KEY_SEED):
          break
      l = x + 2
      seed_bytes += int(CONTENT_KEY_SEED[x:l], 16).to_bytes(1, "big")

    # sha a
    # SHA of the truncatedKeySeed and the keyIdAsBytes
    sha = hashlib.sha256()
    sha.update(seed_bytes)
    sha.update(key_id)
    shaA = [c for c in sha.digest()]

    # sha b
    # SHA of the truncatedKeySeed, the keyIdAsBytes, and
    # the truncatedKeySeed again.
    sha = hashlib.sha256()
    sha.update(seed_bytes)
    sha.update(key_id)
    sha.update(seed_bytes)
    shaB = [c for c in sha.digest()]

    # sha c
    # SHA of the truncatedKeySeed, the keyIdAsBytes,
    # the truncatedKeySeed again, and the keyIdAsBytes again.
    sha = hashlib.sha256()
    sha.update(seed_bytes)
    sha.update(key_id)
    sha.update(seed_bytes)
    sha.update(key_id)
    shaC = [c for c in sha.digest()]

    AES_KEYSIZE_128 = 16
    content_key = b""
    for i in range(AES_KEYSIZE_128):
      xorA = shaA[i] ^ shaA[i + AES_KEYSIZE_128]
      xorB = shaB[i] ^ shaB[i + AES_KEYSIZE_128]
      xorC = shaC[i] ^ shaC[i + AES_KEYSIZE_128]
      content_key += (xorA ^ xorB ^ xorC).to_bytes(1, byteorder='big')

    return base64.b16encode(content_key)

  # cf https://docs.microsoft.com/en-us/playready/specifications/playready-header-specification#5-key-checksum-algorithm
  # `AESCTR`または`COCKTAIL`モードではchecksumが必要。
  def compute_check_sum(self, kid, content_key):
    # kidは16, 24, 32のいずれかでなければいけない 
    if isinstance(kid, str):
      kid = uuid.UUID(kid).bytes_le
    elif isinstance(kid, uuid.UUID):
      kid = kid.bytes_le

    crypto = AES.new(base64.b16decode(content_key), AES.MODE_ECB)
    return crypto.encrypt(kid)[:8]

  # WRM Header v4.0.0を生成。v4.0.0は一番古いPlayReady SDKからバージョン4のSDKまで対応している。
  # TODO: 複数kidとCUSTOM ATTRIBUTE生成に対応
  def gen_wrm_header(self, kid, content_key, la_url):
    checksum = self.compute_check_sum(kid, content_key)
    le_kid = uuid.UUID(kid).bytes_le
    b64_KID = base64.b64encode(le_kid).decode('utf-8')
    b64_checksum = base64.b64encode(checksum).decode('utf-8')
    wrh = '<WRMHEADER xmlns="http://schemas.microsoft.com/DRM/2007/03/PlayReadyHeader" version="4.0.0.0"><DATA><PROTECTINFO><KEYLEN>16</KEYLEN><ALGID>AESCTR</ALGID></PROTECTINFO>'
    wrh += f"<KID>{b64_KID}</KID>"
    wrh += f"<CHECKSUM>{b64_checksum}</CHECKSUM>"
    wrh += f"<LA_URL>{la_url}</LA_URL>"
    wrh += "</DATA></WRMHEADER>"
    return wrh

  # https://docs.microsoft.com/en-us/playready/specifications/playready-header-specification
  # PlayReadyObjectを生成
  # TODO: 複数kidに対応
  def gen_playready_object(self, wrh):
    wrh = wrh.encode('utf-16le')
    wrh_length = len(wrh)
    overall_block_len = 4
    record_count_len = 2
    record_type_len = 2
    wrh_size_len = 2
    header_size = wrh_length + overall_block_len + record_count_len + record_type_len + wrh_size_len

    return ((header_size).to_bytes(overall_block_len, "little") + # PRO全体のながさ
      (1).to_bytes(record_count_len, "little") + # record数
      (1).to_bytes(record_type_len, "little") + # recordタイプ
      (wrh_length).to_bytes(wrh_size_len, "little") + # wrmheaderのながさ
      wrh # wrmheader本体
    )

