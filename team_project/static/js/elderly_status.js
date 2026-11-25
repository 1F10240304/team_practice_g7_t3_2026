// 待機・マッチング画面
const waitingState = document.getElementById('waiting-state');
const matchedState = document.getElementById('matched-state');
const demoBtn = document.getElementById('demo-match-btn');

// 学生が引き受けたかどうかの確認は、live_update.js（自動更新）がやっている

// デモボタンを押したら、待機画面を消して、完了画面を出す
if (demoBtn) {
    demoBtn.addEventListener('click', () => {
        waitingState.classList.add('hidden');
        matchedState.classList.remove('hidden');
        demoBtn.classList.add('hidden'); // ボタン自身も隠す
    });
}
