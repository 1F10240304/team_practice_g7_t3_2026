// 依頼作成（マイク）画面: 話した言葉を文字にして、下の欄に入れる
const micBtn = document.getElementById('mic-btn');
const micText = document.getElementById('mic-text');
const statusText = document.getElementById('recording-status');
const requestText = document.getElementById('request-text');
const submitBtn = document.getElementById('submit-btn');
const unsupportedText = document.getElementById('mic-unsupported');

// 欄に文字が入ったら「次へ」ボタンを出す
function updateSubmitButton() {
    submitBtn.classList.toggle('hidden', requestText.value.trim() === '');
}
requestText.addEventListener('input', updateSubmitButton);

// ブラウザの音声認識（Chrome などで使える）
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    // 声で入力できないときは、文字で書いてもらう
    micBtn.classList.add('hidden');
    unsupportedText.classList.remove('hidden');
} else {
    const recognition = new SpeechRecognition();
    recognition.lang = 'ja-JP';
    recognition.continuous = true;
    recognition.interimResults = true;

    let isRecording = false;
    let textBeforeRecording = '';

    // 録音中の見た目に切り替える
    function setRecording(recording) {
        isRecording = recording;
        micBtn.classList.toggle('recording', recording); // 赤くしてドクンドクンさせる
        statusText.classList.toggle('hidden', !recording);
        micText.innerText = recording ? '録音中...（押すと止まる）' : 'もう一度話す';
    }

    // 聞き取った言葉を欄に入れる（話している途中の言葉もそのまま見せる）
    recognition.addEventListener('result', (event) => {
        let heard = '';
        for (let i = 0; i < event.results.length; i++) {
            heard += event.results[i][0].transcript;
        }
        requestText.value = textBeforeRecording + heard;
        updateSubmitButton();
    });

    // 話すのをやめて少したつと、ブラウザが自動で止める
    recognition.addEventListener('end', () => setRecording(false));
    recognition.addEventListener('error', () => setRecording(false));

    micBtn.addEventListener('click', () => {
        if (isRecording) {
            recognition.stop();
            return;
        }
        textBeforeRecording = requestText.value;
        recognition.start();
        setRecording(true);
    });
}
