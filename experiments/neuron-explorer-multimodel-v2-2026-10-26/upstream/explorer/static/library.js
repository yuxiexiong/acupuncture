// The experiment archive shares this local, read-only server with the 3D map.
(() => {
  const button = document.createElement('button');
  button.textContent = '全部实验';
  button.id = 'experiment-library';
  button.title = '查看各轮实验、原始回答、能力评分与停止记录';
  button.style.cssText = 'position:fixed;left:12px;bottom:12px;z-index:30;padding:8px 14px;border:1px solid #82aacc;border-radius:5px;background:#172a3d;color:#e7f2ff';
  const dialog = document.createElement('dialog');
  dialog.style.cssText = 'width:min(1440px,95vw);height:90vh;padding:0;border:1px solid #52657d;background:#101723;color:#e7edf5';
  dialog.innerHTML = '<div style="height:38px;display:flex;align-items:center;justify-content:space-between;padding:0 12px;font:14px sans-serif"><span>Acupuncture · 全部实验结果</span><button type="button" aria-label="关闭全部实验">关闭，返回三维图</button></div><iframe title="全部实验结果库" style="width:100%;height:calc(100% - 40px);border:0"></iframe>';
  dialog.querySelector('button').onclick = () => dialog.close();
  button.onclick = () => {
    const frame = dialog.querySelector('iframe');
    if (!frame.src) frame.src = '/library.html';
    dialog.showModal();
  };
  document.body.append(dialog);
  (document.querySelector('header') || document.body).append(button);
})();
