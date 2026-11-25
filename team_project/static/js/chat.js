// チャット: 相手が送ったメッセージを、読み込み直さなくても画面の下に足していく
//
// 数秒ごとにサーバーへ「この番号より新しいメッセージ」を聞き、あれば下に足す。
// ページ全体は読み込み直さないので、入力している途中の文章は消えない。
(() => {
    const log = document.getElementById('chat-log');
    if (!log) return;

    const url = log.dataset.url;
    let lastId = Number(log.dataset.lastId) || 0;
    const INTERVAL = 3000; // 3秒ごとに確認する
    let timer = null;
    let checking = false;

    const scrollToBottom = () => window.scrollTo(0, document.body.scrollHeight);

    // メッセージを1件、画面に足す（文章は textContent で入れるので、HTMLとしては動かない）
    const addMessage = (m) => {
        const row = document.createElement('div');
        row.className = 'flex flex-col ' + (m.mine ? 'items-end' : 'items-start');

        const meta = document.createElement('p');
        meta.className = 'text-xs text-gray-400 mb-1';
        meta.textContent = (m.mine ? '自分' : m.name + 'さん') + '　' + m.time;

        const bubble = document.createElement('p');
        bubble.className = 'max-w-[85%] px-4 py-3 rounded-2xl text-lg whitespace-pre-wrap break-words shadow-sm '
            + (m.mine ? 'bg-orange-500 text-white' : 'bg-white text-gray-800 border border-gray-200');
        bubble.textContent = m.text;

        row.append(meta, bubble);
        log.append(row);
    };

    const check = async () => {
        timer = null;
        if (checking) return;
        checking = true;
        try {
            const res = await fetch(`${url}?after=${lastId}`, {
                headers: { Accept: 'application/json' },
                cache: 'no-store',
            });
            // ログインが切れたときなどはJSONが返らないので、何もせず次を待つ
            if (res.ok && (res.headers.get('Content-Type') || '').includes('application/json')) {
                const data = await res.json();
                if (data.messages.length) {
                    document.getElementById('chat-empty')?.classList.add('hidden');
                    data.messages.forEach(addMessage);
                    lastId = data.messages[data.messages.length - 1].id;
                    scrollToBottom();
                }
                // 相手が依頼を完了にしたら、送る欄を消すために一度だけ読み込み直す
                if (!data.can_send && document.getElementById('chat-text')) {
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
        clearTimeout(timer);
        timer = null;
        if (!document.hidden) check(); // タブに戻ってきたら、すぐに確認する
    });

    // Ctrl+Enter（Macは ⌘+Enter）でも送れるようにする
    const textarea = document.getElementById('chat-text');
    textarea?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            textarea.form.requestSubmit();
        }
    });

    scrollToBottom();
    schedule();
})();
