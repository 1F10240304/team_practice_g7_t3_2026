// 自動更新: 相手（学生・高齢者）が操作したら、リロードしなくても画面が新しくなる
//
// 数秒ごとにサーバーへ「今の版」を聞き、ページを開いたときの版と違っていたら
// ページを読み込み直す。何も変わっていなければ何もしないので、画面はチカつかない。
(() => {
    const el = document.getElementById('live-update');
    if (!el) return;

    const url = el.dataset.url;
    const firstVersion = el.dataset.version;
    const INTERVAL = 4000; // 4秒ごとに確認する
    let timer = null;
    let checking = false; // 確認中に二重で確認しないようにする

    // 文字を入力している途中に読み込み直すと、書いた内容が消えてしまう
    const isTyping = () => {
        const a = document.activeElement;
        return a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable);
    };

    const check = async () => {
        timer = null;
        if (checking) return;
        checking = true;
        try {
            const res = await fetch(url, {
                headers: { Accept: 'application/json' },
                cache: 'no-store',
            });
            // ログインが切れたときなどはJSONが返らないので、何もせず次を待つ
            if (res.ok && (res.headers.get('Content-Type') || '').includes('application/json')) {
                const data = await res.json();
                if (data.version !== firstVersion && !isTyping()) {
                    location.reload();
                    return;
                }
            }
        } catch (e) {
            // 通信が一時的に切れても、次の確認で取り戻せるので何もしない
        } finally {
            checking = false;
        }
        schedule();
    };

    const schedule = () => {
        // タブが裏にあるあいだは確認しない（ムダな通信を減らす）
        if (!document.hidden && timer === null) {
            timer = setTimeout(check, INTERVAL);
        }
    };

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            clearTimeout(timer);
            timer = null;
        } else {
            // タブに戻ってきたら、すぐに確認する
            clearTimeout(timer);
            check();
        }
    });

    schedule();
})();
