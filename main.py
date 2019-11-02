# -*- coding: utf-8 -*-

from playready import PlayReadyLib

play_ready_lib = playready.PlayReadyLib()
key_id = "11112222-3333-4444-5555-666677778888"
la_url = "play ready la url"

content_key = play_ready_lib.gen_content_key(key_id)
checksum = play_ready_lib.compute_check_sum(key_id, content_key)
wrm_header = play_ready_lib.gen_wrm_header(key_id, content_key, la_url)
playready_object = play_ready_lib.gen_playready_object(wrm_header)

print(f"content_key: {content_key}")
print(f"checksum: {checksum}")
print(f"wrmheader: {wrm_header}")
print(f"playready object: {playready_object}")
