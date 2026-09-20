const { createApp } = Vue

createApp({
  data () {
    return {
      questions: [],
      formValues: {}, // ユーザー回答を格納
      sending: false, // ボタンのdisable制御
      result: [] // 結果表示用
    }
  },

  mounted () {
    const aiTypes = [
      { id: 'button-openai', llm: 'openai' },
      { id: 'button-google', llm: 'google' },
      { id: 'button-groq', llm: 'groq' },
      { id: 'button-self', llm: 'self' }
    ]
    aiTypes.forEach(({ id, llm }) => {
      const btn = document.getElementById(id)
      if (btn) {
        btn.addEventListener('click', () => {
          btn.disabled = true
          this.loadQuestions('some', llm)
        })
      }
    })
    const btn = document.getElementById('start-button')
    if (btn) {
      btn.addEventListener('click', () => {
        btn.disabled = true
        this.loadQuestions('some')
      })
    }
    const btt = document.getElementById('start-button-t')
    if (btt) {
      btt.addEventListener('click', () => {
        btt.disabled = true
        this.loadQuestions('travel')
      })
    }
    const retryBtn = document.getElementById('retry-button')
    if (retryBtn) {
      retryBtn.addEventListener('click', function () {
        // 質問先頭にスクロール
        const qTop = document.getElementById('vue-question-area')
        if (qTop) {
          qTop.scrollIntoView({ behavior: 'smooth' })
        }
      })
    }
  },

  methods: {
    handleFetchResponse (res) {
      if (res.status === 429) {
        alert('ビジーです。再度実行してください')
        throw new Error('Too Many Requests')
      } else if (res.status === 403) {
        alert('エラー発生。トップ画面からやり直してください')
        throw new Error('Service Unavailable')
      } else if (res.status !== 200) {
        alert('エラー発生')
        throw new Error(`HTTP error: ${res.status}`)
      }
      return res
    },
    /* `loadQuestions` is a method in the Vue app that is responsible for fetching questions from the
    server based on a specified theme. Here is a breakdown of what `loadQuestions` is doing: */
    loadQuestions (theme, llmType = 'openai') {
      const titleField = document.getElementById('title')?.value || '任意テーマ'
      const extraData = {
        theme: document.getElementById('theme')?.value.trim() || '',
        instruction: document.getElementById('instruction')?.value.trim() || '',
        sendInstruction:
          document.getElementById('sendInstruction')?.value.trim() || '',
        userAdvice: document.getElementById('userAdvice')?.value.trim() || '',
        aillm: llmType // ここでAI種別を渡す
      }
      let url = '/get_questions'
      if (theme === 'travel') {
        url = '/get_questions_travel'
      }

      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: titleField,
          ...extraData
        })
      })
        .then(this.handleFetchResponse)
        .then(res => res.json())
        .then(data => {
          this.questions = data.questions || []
          this.$nextTick(() => {
            const vueArea = document.getElementById('vue-question-area')
            if (vueArea) {
              vueArea.scrollIntoView({ behavior: 'smooth', block: 'start' })
              window.scrollBy(0, 100)
            }
          })
          this.questions.forEach(q => {
            const key = 'q' + q.id
            if (q.type === 'multiple') {
              this.formValues[key] = []
            } else {
              this.formValues[key] = ''
            }
          })
        })
        .catch(err => {
          alert('質問の取得に失敗しました。')
          console.error('質問取得失敗:', err)
        })
    },

    getResult (llmType) {
      this.sending = true
      const extraData = {
        title: document.getElementById('title')?.value.trim() || '',
        theme: document.getElementById('theme')?.value.trim() || '',
        instruction: document.getElementById('instruction')?.value.trim() || '',
        sendInstruction:
          document.getElementById('sendInstruction')?.value.trim() || '',
        userAdvice: document.getElementById('userAdvice')?.value.trim() || ''
      }

      const answers = this.questions.map(q => {
        let value = this.formValues['q' + q.id]
        return {
          question: q.text,
          answer: value || ''
        }
      })

      const payload = {
        answer: {
          theme: document.getElementById('theme')?.value || '',
          sendInstruction:
            document.getElementById('sendInstruction')?.value || '',
          aillm: llmType,
          answers: answers,
          ...extraData
        }
      }

      fetch('/get_result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
        .then(this.handleFetchResponse)
        .then(res => res.json())
        .then(data => {
          this.displayResult(data.result)
        })
        .catch(err => {
          alert('結果取得に失敗しました。')
          console.error('結果取得失敗:', err)
        })
        .finally(() => {
          this.sending = false
        })
    },
    scrollToTop () {
      const qTop = document.getElementById('vue-question-area')
      if (qTop) {
        qTop.scrollIntoView({ behavior: 'smooth' })
      }
    },
    displayResult (result) {
      this.result = result.map(rec => {
        const keywords = this.extractSearchKeywords()
        return {
          ...rec,
          googleSearchUrl: `https://www.google.com/search?q=${encodeURIComponent(
            rec.destination + 'を' + keywords + 'で'
          )}`
        }
      })

      // おすすめの提案見出しにスクロール
      this.$nextTick(() => {
        const header = document.querySelector('.results-header')
        if (header) {
          header.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      })
    },

    extractSearchKeywords () {
      const form = document.getElementById('questionsArea')
      const inputs = form.querySelectorAll('input, select, textarea')
      const values = []

      inputs.forEach(el => {
        if (el.type === 'checkbox' && el.checked) {
          values.push(el.value)
        } else if (el.type !== 'checkbox' && el.value) {
          values.push(el.value)
        }
      })

      return values.join(' ')
    }
  }
}).mount('#vue-question-area')
