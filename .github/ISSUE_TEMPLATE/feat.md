---
name: Feat
about: "✨ Feat(페이지 경로 또는 컴포넌트): 새로운 기능 추가 또는 기능 업데이트"
title: "[feat]"
labels: ''
assignees: ''

---

## ✨ 구현 할 기능

- [ ]
- [ ]
- [ ]

<br>

### 📕 레퍼런스

```
---
name: Feat
about: "✨ Feat(페이지 경로 또는 컴포넌트): 새로운 기능 추가 또는 기능 업데이트"
title: "[feat]"
labels: ''
assignees: ''

---

## 예시

### 1. 프론트엔드에서 요청 예시

```http
GET /api/videos/
Authorization: Bearer <access_token>
```

- **request body 없음**
- 토큰만 헤더에 포함

---

### 2. 만약 POST로 body에 뭔가를 꼭 담아야 한다면 (비권장)

일반적으로 권장하지 않지만,  
특별한 이유로 body에 사용자 정보를 담고 싶다면 아래와 같이 할 수 있습니다.

```json
{
  "user_id": "1234567890"
}
```

하지만,  
- 이 경우에도 보안상 토큰을 헤더에 담는 것이 표준입니다.
- user_id를 body에 담는 것은 권장되지 않습니다.

---

## 결론

- **표준 방식**:  
  - request body 없이,  
  - Authorization 헤더에 토큰만 담아서 요청

- **예시 (Python requests)**:
  ```python
  import requests

  headers = {
      "Authorization": "Bearer <access_token>"
  }
  response = requests.get("https://your-api.com/api/videos/", headers=headers)
  ```

---

### 혹시 정말로 request body 예시가 필요하다면,  
아래처럼 작성할 수 있습니다(비권장):

```json
<code_block_to_apply_changes_from>
```

하지만,  
**OAuth 표준은 헤더 사용**이므로,  
가능하면 헤더에 토큰을 담아주세요!

---

필요하신 방식(헤더/바디)이나 추가 정보가 있다면 말씀해 주세요.  
API 명세서 예시, Django view 예시 등도 도와드릴 수 있습니다!