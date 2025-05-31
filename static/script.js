
// 質問生成リクエスト用のJSON（例としてサンプル使用）
const questionRequest = {
    title: "旅行先"
};

/*
document.addEventListener("DOMContentLoaded", function () {
    const startBtn = document.getElementById("start-button");
    if (!startBtn) {
        console.error("start-button が見つかりません");
        return;
    }

    startBtn.addEventListener("click", function () {
        startBtn.disabled = true;
        const originalText = startBtn.textContent;
        startBtn.textContent = "処理中...";

        fetch("/get_questions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(questionRequest)
        })
            .then(response => response.json())
            .then(data => {
                displayQuestions(data);
            })
            .catch(error => {
                console.error("エラー:", error);
                alert("質問の取得に失敗しました。");
            })
            .finally(() => {
                startBtn.disabled = false;
                startBtn.textContent = originalText;
            });
    });
});



function displayQuestions(data) {
    console.log("受信データ:", data);

    const area = document.getElementById("questionsArea");
    // area.innerHTML = "";  // 初期化

    // ヘッダを追加（線が上に来るように）
    const header = document.createElement("div");
    header.className = "section-header";
    header.textContent = "アンケートに答えてください";
    area.appendChild(header);

    if (!data || !Array.isArray(data.questions)) {
        console.error("質問データが不正です:", data);
        return;
    }

    data.questions.forEach(q => {
        const qDiv = document.createElement("div");
        qDiv.className = "question-block";

        const qText = document.createElement("p");
        qText.textContent = q.text;
        qDiv.appendChild(qText);

        if (q.type === "single") {
            const select = document.createElement("select");
            select.name = `q${q.id}`;

            // 未選択のオプションを最初に追加
            const emptyOption = document.createElement("option");
            emptyOption.value = "";
            emptyOption.textContent = "選択してください";
            select.appendChild(emptyOption);

            // 実際の選択肢を追加
            q.choices.forEach(choice => {
                const option = document.createElement("option");
                option.value = choice;
                option.textContent = choice;
                select.appendChild(option);
            });

            qDiv.appendChild(select);

        } else if (q.type === "multiple" && Array.isArray(q.choices) && q.choices.length > 0) {
            const choicesContainer = document.createElement("div");
            choicesContainer.className = "choices-container";

            q.choices.forEach(choice => {
                const label = document.createElement("label");
                const input = document.createElement("input");
                input.type = "checkbox";
                input.name = `q${q.id}`;
                input.value = choice;

                label.appendChild(input);
                label.appendChild(document.createTextNode(" " + choice));
                choicesContainer.appendChild(label);
            });

            qDiv.appendChild(choicesContainer);
        } else if (q.type === "text1") {
            const textarea = document.createElement("textarea");
            textarea.name = `q${q.id}`;
            textarea.rows = 4;
            textarea.cols = 50;
            // textarea.maxLength = 100;
            textarea.placeholder = "ここに入力してください";
            qDiv.appendChild(textarea);
        } else {
            const input = document.createElement("input");
            input.type = "text";
            input.name = `q${q.id}`;
            qDiv.appendChild(input);
        }

        area.appendChild(qDiv);
    });

    const buttonGroup = document.createElement("div");
    buttonGroup.style.display = "flex";
    buttonGroup.style.gap = "12px";
    buttonGroup.style.marginTop = "20px";

    const buttonTypes = ["openai", "google", "self"];

    buttonTypes.forEach(name => {
        const button = document.createElement("button");
        button.type = "button";
        button.name = "btn_" + name;
        button.textContent = "送信(" + name + ")";
        button.addEventListener("click", getResult);
        buttonGroup.appendChild(button);
    });

    area.appendChild(buttonGroup);

}
*/

function getResult(event) {
    if (event) event.preventDefault();

    // 結果エリアをクリア
    const resultDiv = document.getElementById("resultsArea");
    resultDiv.innerHTML = "";

    // ボタンを取得・disable・文言変更
    const submitButton = event.target;
    submitButton.disabled = true;
    const originalText = submitButton.textContent;
    submitButton.textContent = "処理中...";

    const form = document.getElementById("questionsArea");
    const formData = new FormData(form);

    tit = document.getElementById("title");
    tit = tit.value;
    aillm = event.target.name;

    const answers = [];
    const grouped = {};

    for (let [key, value] of formData.entries()) {
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(value);
    }

    for (let qid in grouped) {
        const qTextElem = form.querySelector(`input[name="${qid}"], textarea[name="${qid}"]`);
        const qContainer = qTextElem?.closest(".question-block");
        const qLabel = qContainer?.querySelector("p")?.textContent || "";
        answers.push({ answer: grouped[qid].join(", "), question: qLabel });
    }

    const answer = {
        title: tit,
        aillm: aillm,
        answers: answers
    };

    fetch("/get_result", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer })
    })
        .then(response => response.json())
        .then(data => {
            displayResult(data.result);
        })
        .catch(error => {
            console.error("送信エラー:", error);
            resultDiv.innerHTML = "<p style='color:red;'>エラーが発生しました。</p>";
        })
        .finally(() => {
            // ボタンを元に戻す
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        });
}

function displayResultX(result) {
    const resultDiv = document.getElementById("resultsArea");
    resultDiv.innerHTML = "";

    const titleDiv = document.createElement("div");
    titleDiv.className = "results-header";

    const h3 = document.createElement("h3");
    h3.textContent = "おすすめの" + document.getElementById("title").text;
    titleDiv.appendChild(h3);

    resultDiv.appendChild(titleDiv);


    const list = document.createElement("ul");

    result.forEach(rec => {
        const item = document.createElement("li");

        const title = document.createElement("strong");
        title.textContent = `${rec.destination}（スコア: ${rec.score}）`;

        const desc = document.createElement("p");
        desc.textContent = rec.description;

        const link = document.createElement("a");
        link.href = rec.url;
        link.target = "_blank";
        link.textContent = rec.url;


        const queryText = `${rec.destination} ${extractSearchKeywordsFrom()}`;

        const searchLink = document.createElement("a");
        searchLink.href = `https://www.google.com/search?q=${encodeURIComponent(queryText)}`;
        searchLink.target = "_blank";
        searchLink.textContent = `${rec.destination} をこの条件でGoogle検索`;
        searchLink.style.display = "block";
        searchLink.style.marginTop = "0.2em";;

        item.appendChild(title);
        item.appendChild(document.createElement("br"));
        item.appendChild(desc);
        item.appendChild(link);
        item.appendChild(searchLink);  // ← ここで追加

        list.appendChild(item);
    });

    resultDiv.appendChild(list);

    // ▼ 回答からやり直しボタン追加
    const retryBtn = document.createElement("button");
    retryBtn.textContent = "回答からやり直し";
    retryBtn.style.marginLeft = "1em";
    retryBtn.addEventListener("click", () => {
        resultDiv.innerHTML = ""; // 結果を消す
        document.getElementById("questionsArea").style.display = "block"; // 質問フォームを再表示

        // アンケートタイトルまでスクロール
        const questionsArea = document.getElementById("questionsArea");
        if (questionsArea) {
            questionsArea.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });
    resultDiv.appendChild(retryBtn);

    // スクロール処理：最初のおすすめを中央に近づけて表示
    setTimeout(() => {
        resultDiv.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 300);
}

// フォーム要素から直接値を取得する
// DOMから必要な値を抽出する関数
function extractSearchKeywordsFrom() {
    const form = document.getElementById("questionsArea");
    const blocks = form.querySelectorAll(".question-block");

    const parts = [];

    blocks.forEach(block => {
        const question = block.querySelector("p")?.textContent?.trim() || "";

        // 回答値を取得（textareaはスキップ）
        const textarea = block.querySelector("textarea");
        if (textarea) return;

        let value = "";

        const input = block.querySelector("input[type='text']");
        if (input) {
            value = input.value.trim();
        }

        const select = block.querySelector("select");
        if (select) {
            value = select.value;
        }

        const checkboxes = block.querySelectorAll("input[type='checkbox']:checked");
        if (checkboxes.length > 0) {
            value = Array.from(checkboxes).map(cb => cb.value).join(" ");
        }

        if (question && value) {
            parts.push(`${question} ${value}`);
        }
    });

    return parts.join(" ");
}