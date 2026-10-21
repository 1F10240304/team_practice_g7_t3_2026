// 待機・マッチング画面
const waitingState = document.getElementById('waiting-state');
const matchedState = document.getElementById('matched-state');
const demoBtn = document.getElementById('demo-match-btn');

// 待っているあいだは15秒ごとに読み込み直して、学生が引き受けたか確かめる
const reloadTimer = waitingState.classList.contains('hidden')
    ? null
    : setTimeout(() => location.reload(), 15000);

// デモボタンを押したら、待機画面を消して、完了画面を出す
if (demoBtn) {
    demoBtn.addEventListener('click', () => {
        clearTimeout(reloadTimer); // 読み込み直すとデモの表示が戻ってしまうので止める
        waitingState.classList.add('hidden');
        matchedState.classList.remove('hidden');
        demoBtn.classList.add('hidden'); // ボタン自身も隠す
    });
}
