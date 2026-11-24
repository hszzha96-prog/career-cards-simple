class Component extends DCLogic {
  state = { view: 'card', sel: 0, tab: 'elig', filter: 'all', checks: {}, practiced: {}, sound: true, toastMsg: '', tl: null };

  setCard = (el) => { this.cardEl = el; };
  setAside = (el) => { this.asideEl = el; };
  setPanel = (el) => { this.panelEl = el; };
  setTabs = (el) => { this.tabsEl = el; };
  setToast = (el) => { this.toastEl = el; };
  setBurst = (el) => { this.burstEl = el; };
  setRoot = (el) => { this.rootEl = el; };
  setMain = (el) => { this.mainEl = el; };
  setGrid = (el) => { this.gridEl = el; };
  setSweep = (el) => { this.sweepEl = el; };
  setFx = (el) => { this.fxEl = el; };
  fxIndex = 0;
  sweepAnims = [];

  onPress = (e) => {
    this.play('click');
    const root = this.rootEl;
    const fx = this.fxEl;
    if (!root || !fx || !fx.children.length) return;
    const r = root.getBoundingClientRect();
    const k = r.width ? root.offsetWidth / r.width : 1;
    const x = (e.clientX - r.left) * k;
    const y = (e.clientY - r.top) * k;
    const pool = fx.children[this.fxIndex++ % fx.children.length];
    pool.style.transform = 'translate(' + x + 'px, ' + y + 'px)';
    const kids = pool.children;
    const n = kids.length - 1;
    const spin = Math.random() * Math.PI * 2;
    for (let i = 0; i < n; i++) {
      const a = spin + (i / n) * Math.PI * 2 + (Math.random() - 0.5) * 0.5;
      const d = 22 + Math.random() * 30;
      const s = 0.5 + Math.random() * 0.8;
      this.motion(kids[i], [
        { opacity: 1, transform: 'translate(0, 0) scale(' + s + ')' },
        { opacity: 0, transform: 'translate(' + Math.cos(a) * d + 'px, ' + (Math.sin(a) * d + 6) + 'px) scale(0.2)' }
      ], 520 + Math.random() * 200, 0, 'cubic-bezier(.15,.85,.25,1)');
    }
    this.motion(kids[n], [
      { opacity: 0.9, transform: 'scale(0.2)' },
      { opacity: 0, transform: 'scale(1.25)' }
    ], 460, 0, 'cubic-bezier(.2,.8,.2,1)');
  };

  componentDidMount() {
    try {
      const saved = JSON.parse(window.localStorage.getItem('career-desk-v1') || '{}');
      const snd = window.localStorage.getItem('career-desk-sound');
      this.setState({ checks: saved.checks || {}, practiced: saved.practiced || {}, sound: snd !== '0' });
    } catch (e) {}
    this.measureTab();
  }

  componentDidUpdate(prevProps, prevState) {
    const st = this.state;
    const viewChanged = st.view !== prevState.view;
    if (viewChanged) this.transition(st.view === 'overview' ? 1 : -1);
    const switched = st.sel !== prevState.sel || (st.view === 'card' && prevState.view !== 'card');
    if (switched && !viewChanged) {
      this.motion(this.cardEl, [{ opacity: 0, transform: 'translateY(14px)' }, { opacity: 1, transform: 'none' }], 320, 0, 'steps(5, end)');
    }
    if (switched && this.asideEl) Array.prototype.forEach.call(this.asideEl.children, (c, i) => {
      this.motion(c, [{ opacity: 0, transform: 'translateX(16px)' }, { opacity: 1, transform: 'none' }], 360, (viewChanged ? 260 : 70) + i * 60);
    });
    if (st.tab !== prevState.tab && !switched) {
      this.motion(this.panelEl, [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], 260);
    }
    if (st.tab !== prevState.tab || switched) this.measureTab();
  }

  motion(el, frames, duration, delay, easing) {
    if (!el || !el.animate) return null;
    try {
      if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return null;
      return el.animate(frames, { duration: duration, delay: delay || 0, easing: easing || 'cubic-bezier(.2,.8,.2,1)', fill: 'backwards' });
    } catch (e) { return null; }
  }

  transition(dir) {
    this.play('whoosh');
    this.sweepAnims.forEach((a) => { try { a.cancel(); } catch (e) {} });
    this.sweepAnims = [];
    // 星空渐变遮罩 + 泡泡与星屑向上消散，掩住新旧页面的切换
    if (this.sweepEl) Array.prototype.forEach.call(this.sweepEl.children, (el) => {
      let a = null;
      if (el.classList.contains('veil')) {
        a = this.motion(el, [{ opacity: 0 }, { opacity: 0.82, offset: 0.32 }, { opacity: 0 }], 820, 0, 'ease-in-out');
      } else {
        const delay = Number(el.getAttribute('data-d')) || 0;
        const rise = Number(el.getAttribute('data-r')) || 80;
        const drift = (Number(el.getAttribute('data-x')) || 0) * dir;
        a = this.motion(el, [
          { opacity: 0, transform: 'translate(0, 24px) scale(0.3)' },
          { opacity: 0.9, transform: 'translate(' + drift * 0.4 + 'px, ' + (-rise * 0.35) + 'px) scale(1)', offset: 0.4 },
          { opacity: 0, transform: 'translate(' + drift + 'px, ' + (-rise) + 'px) scale(1.6)' }
        ], 950, delay, 'cubic-bezier(.2,.7,.3,1)');
      }
      if (a) this.sweepAnims.push(a);
    });
    const ghost = (blur, bright, y, op) => 'blur(' + blur + 'px) brightness(' + bright + ') drop-shadow(0 ' + (-y) + 'px 0 rgba(181,156,255,' + op + '))';
    this.motion(this.mainEl, [
      { opacity: 0, transform: 'translateY(10px) scale(0.985)', filter: ghost(10, 1.35, 16, 0.4) },
      { opacity: 0.9, transform: 'translateY(2px) scale(0.995)', filter: ghost(3, 1.1, 6, 0.22), offset: 0.5 },
      { opacity: 1, transform: 'none', filter: ghost(0, 1, 0, 0) }
    ], 760, 220);
    if (dir > 0 && this.gridEl) Array.prototype.forEach.call(this.gridEl.querySelectorAll('.plot'), (c, i) => {
      this.motion(c, [
        { opacity: 0, transform: 'translateY(18px) scale(0.8)' },
        { opacity: 1, transform: 'translateY(-4px) scale(1.04)', offset: 0.7 },
        { opacity: 1, transform: 'none' }
      ], 460, 240 + i * 26, 'steps(6, end)');
    });
  }

  measureTab() {
    const box = this.tabsEl;
    if (!box) return;
    const order = ['elig', 'match', 'prep', 'proj'];
    const btn = box.querySelectorAll('[role="tab"]')[order.indexOf(this.state.tab)];
    if (!btn) return;
    const tl = { l: btn.offsetLeft, w: btn.offsetWidth };
    const old = this.state.tl;
    if (!old || old.l !== tl.l || old.w !== tl.w) this.setState({ tl: tl });
  }

  save() {
    try {
      window.localStorage.setItem('career-desk-v1', JSON.stringify({ checks: this.state.checks, practiced: this.state.practiced }));
      window.localStorage.setItem('career-desk-sound', this.state.sound ? '1' : '0');
    } catch (e) {}
  }

  play(kind) {
    if (!this.state.sound) return;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      const ctx = this.ac || (this.ac = new AC());
      if (ctx.state === 'suspended') ctx.resume();
      const SOUNDS = {
        tick: [[1180, 1180, 0, 0.045, 0.035]],
        switch: [[520, 700, 0, 0.09, 0.05]],
        pop: [[620, 980, 0, 0.11, 0.07]],
        undo: [[700, 420, 0, 0.12, 0.05]],
        chime: [[880, 880, 0, 0.5, 0.06], [1318.5, 1318.5, 0.11, 0.6, 0.06], [1760, 1760, 0.22, 0.7, 0.045]],
        click: [[3200, 2600, 0, 0.05, 0.035], [5200, 4800, 0, 0.03, 0.015]]
      };
      if (kind === 'whoosh') {
        const len = Math.floor(ctx.sampleRate * 0.55);
        const buf = ctx.createBuffer(1, len, ctx.sampleRate);
        const ch = buf.getChannelData(0);
        for (let i = 0; i < len; i++) ch[i] = Math.random() * 2 - 1;
        const src = ctx.createBufferSource();
        src.buffer = buf;
        const bp = ctx.createBiquadFilter();
        bp.type = 'bandpass';
        bp.Q.value = 1.4;
        const t0 = ctx.currentTime;
        bp.frequency.setValueAtTime(380, t0);
        bp.frequency.exponentialRampToValueAtTime(3400, t0 + 0.42);
        const g = ctx.createGain();
        g.gain.setValueAtTime(0.0001, t0);
        g.gain.exponentialRampToValueAtTime(0.08, t0 + 0.16);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.52);
        src.connect(bp).connect(g).connect(ctx.destination);
        src.start(t0);
        src.stop(t0 + 0.55);
        return;
      }
      (SOUNDS[kind] || SOUNDS.tick).forEach((n) => {
        const t0 = ctx.currentTime + n[2];
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.type = kind === 'click' ? 'triangle' : 'sine';
        o.frequency.setValueAtTime(n[0], t0);
        o.frequency.exponentialRampToValueAtTime(n[1], t0 + n[3] * 0.6);
        g.gain.setValueAtTime(0.0001, t0);
        g.gain.exponentialRampToValueAtTime(n[4], t0 + 0.008);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + n[3]);
        o.connect(g).connect(ctx.destination);
        o.start(t0);
        o.stop(t0 + n[3] + 0.02);
      });
    } catch (e) {}
  }

  toast(msg) {
    this.setState({ toastMsg: msg }, () => {
      const el = this.toastEl;
      if (!el || !el.animate) return;
      try {
        if (this.toastAnim) this.toastAnim.cancel();
        this.toastAnim = el.animate([
          { opacity: 0, transform: 'translate(-50%, 10px) scale(0.96)' },
          { opacity: 1, transform: 'translate(-50%, 0) scale(1)', offset: 0.1 },
          { opacity: 1, transform: 'translate(-50%, 0) scale(1)', offset: 0.82 },
          { opacity: 0, transform: 'translate(-50%, -6px) scale(0.98)' }
        ], { duration: 1900, easing: 'ease-out' });
      } catch (e) {}
    });
  }

  celebrate() {
    const box = this.burstEl;
    if (!box || !box.animate) return;
    Array.prototype.forEach.call(box.children, (s, i, all) => {
      const a = (i / all.length) * Math.PI * 2;
      const r = 38 + (i % 3) * 14;
      this.motion(s, [
        { opacity: 1, transform: 'translate(-50%, -50%) scale(1)' },
        { opacity: 0, transform: 'translate(' + (Math.cos(a) * r - 3) + 'px, ' + (Math.sin(a) * r - 3) + 'px) scale(0.3)' }
      ], 760, (i % 4) * 25);
    });
  }

  xpOf(st) {
    let n = 0;
    CARDS.forEach((d) => {
      d.gaps.forEach((g, k) => { if (st.checks[d.fid + '|g|' + k]) n++; });
      d.qs.forEach((q, k) => { if (st.practiced[d.fid + '|q|' + k]) n++; });
    });
    return n * 10;
  }

  toggle(field, key, label, total, doneMsg) {
    const before = Math.floor(this.xpOf(this.state) / 100) + 1;
    const map = Object.assign({}, this.state[field]);
    const on = !map[key];
    if (on) map[key] = true; else delete map[key];
    const upd = {};
    upd[field] = map;
    this.setState(upd, () => this.save());
    const prefix = key.slice(0, key.lastIndexOf('|') + 1);
    let n = 0;
    for (let i = 0; i < total; i++) if (map[prefix + i]) n++;
    const nextState = Object.assign({}, this.state, upd);
    const after = Math.floor(this.xpOf(nextState) / 100) + 1;
    if (on && after > before) {
      this.play('chime');
      this.toast('升级！岗位小镇 Lv.' + after);
      this.celebrate();
    } else if (on && n === total) {
      this.play('chime');
      this.toast(doneMsg);
      if (field === 'checks') this.celebrate();
    } else {
      this.play(on ? 'pop' : 'undo');
      this.toast((on ? label[0] : label[1]) + ' ' + n + '/' + total);
    }
  }

  renderVals() {
    const accent = this.props.accent ?? '#F2C14E';
    const st = this.state;
    const CATS = {
      candidate: { label: '候选', bg: 'rgba(108,180,255,.15)', fg: '#8CC4FF' },
      applied: { label: '已投', bg: 'rgba(123,211,137,.15)', fg: '#8FE09C' },
      incomplete: { label: '待补证据', bg: 'rgba(242,193,78,.15)', fg: '#F2C14E' },
      closed: { label: '已结束', bg: 'rgba(168,163,191,.15)', fg: '#B9B4CF' },
      trash: { label: '废纸篓', bg: 'rgba(240,122,160,.15)', fg: '#F59AB8' }
    };
    const GROUPS = [
      { key: 'candidate', label: '候选', cats: ['candidate'] },
      { key: 'applied', label: '已投', cats: ['applied'] },
      { key: 'incomplete', label: '待补证据', cats: ['incomplete'] },
      { key: 'archive', label: '归档', cats: ['closed', 'trash'] }
    ];
    const go = (i) => { this.play('switch'); this.setState({ sel: i, view: 'card' }); };
    const pct = (a, b) => (b ? Math.round(a / b * 100) : 0);
    const STAGE_NAMES = ['种子', '发芽', '长叶', '含苞', '开花', '枯萎 · 归档'];
    const stageOf = (done, total) => (done === 0 ? 0 : done / total < 0.34 ? 1 : done / total < 0.67 ? 2 : done < total ? 3 : 4);
    const boxOn = 'background: #7BD389; border-color: #7BD389';

    const items = CARDS.map((d, i) => {
      const c = CATS[d.cat];
      let gDone = 0;
      let qDone = 0;
      d.gaps.forEach((g, k) => { if (st.checks[d.fid + '|g|' + k]) gDone++; });
      d.qs.forEach((q, k) => { if (st.practiced[d.fid + '|q|' + k]) qDone++; });
      const total = d.gaps.length + d.qs.length;
      const done = gDone + qDone;
      const archived = d.cat === 'closed' || d.cat === 'trash';
      const stage = archived ? 5 : stageOf(done, total);
      return Object.assign({}, d, {
        done: done,
        total: total,
        stage: stage,
        crop: CROPS[stage],
        stageName: STAGE_NAMES[stage],
        plotCls: archived ? 'plot is-dim' : 'plot',
        fillStyle: 'fill: ' + d.color,
        n: String(i + 1).padStart(2, '0'),
        statusStyle: 'background: ' + c.bg + '; color: ' + c.fg,
        tileStyle: 'background: ' + d.color,
        bigTileStyle: 'background: ' + d.color,
        strokeStyle: 'stroke: ' + d.color,
        gDone: gDone,
        gTotal: d.gaps.length,
        gBarStyle: 'width: ' + pct(gDone, d.gaps.length) + '%; background: #6CB4FF',
        cls: 'dock-item' + (d.cat === 'closed' || d.cat === 'trash' ? ' is-dim' : '') + (st.view === 'card' && st.sel === i ? ' is-active' : ''),
        pick: () => go(i)
      });
    });

    const raw = items[Math.min(st.sel, items.length - 1)];
    const qItems = raw.qs.map((q, k) => {
      const key = raw.fid + '|q|' + k;
      const on = !!st.practiced[key];
      return {
        zh: q.zh, en: q.en, on: on, pressed: on ? 'true' : 'false',
        boxCls: on ? 'box round on' : 'box round',
        boxStyle: on ? boxOn : '',
        textCls: on ? 'done-text' : '',
        pick: () => this.toggle('practiced', key, ['施肥 +10 XP · 已练', '撤回 −10 XP · 已练'], raw.qs.length, raw.co + ' 的预练题全部练完 +10 XP')
      };
    });
    const qDone = qItems.filter((q) => q.on).length;
    const gapItems = raw.gaps.map((g, k) => {
      const key = raw.fid + '|g|' + k;
      const on = !!st.checks[key];
      return {
        text: g, on: on, pressed: on ? 'true' : 'false',
        boxCls: on ? 'box on' : 'box',
        boxStyle: on ? boxOn : '',
        textCls: on ? 'done-text' : '',
        pick: () => this.toggle('checks', key, ['浇水 +10 XP · 已核', '撤回 −10 XP · 已核'], raw.gaps.length, raw.co + ' 的待核事项全部完成 +10 XP')
      };
    });

    const cur = Object.assign({}, raw, {
      srcCount: raw.sources.length,
      dims: raw.dims.map((d) => ({
        name: d.name, status: d.status, note: d.note,
        dotStyle: 'background: ' + (d.ok ? '#16A34A' : '#D97706'),
        statusStyle: 'color: ' + (d.ok ? '#166534' : '#8A4B08')
      })),
      steps: raw.steps.map((s, k) => ({ k: k + 1, t: s.t, x: s.x })),
      projects: raw.projects.map((p) => ({
        name: p.name, sub: p.sub, intro: p.intro, boundary: p.boundary,
        bullets: p.bullets.map((b) => '· ' + b).join('\n')
      })),
      qItems: qItems,
      qDone: qDone,
      qTotal: qItems.length,
      qBarStyle: 'width: ' + pct(qDone, qItems.length) + '%; background: #7BD389',
      gapItems: gapItems,
      gBarStyle: raw.gBarStyle
    });

    const TABS = [
      { key: 'elig', label: '资格核验' },
      { key: 'match', label: '能力匹配' },
      { key: 'prep', label: '行动与预练' },
      { key: 'proj', label: '经历与材料' }
    ];
    const measured = !!st.tl;
    const tabs = TABS.map((t) => ({
      label: t.label,
      sel: st.tab === t.key ? 'true' : 'false',
      cls: st.tab === t.key ? 'tab is-on' : 'tab',
      lineStyle: (!measured && st.tab === t.key) ? 'border-bottom-color: ' + accent : '',
      pick: () => this.setState({ tab: t.key })
    }));

    const catCounts = Object.keys(CATS).map((k) => {
      const count = CARDS.filter((d) => d.cat === k).length;
      return { label: CATS[k].label, count: count, barStyle: 'width: ' + pct(count, CARDS.length) + '%; background: ' + CATS[k].fg };
    });

    const inG = (cats) => items.filter((it) => cats.indexOf(it.cat) >= 0);
    const field = (title, en, cats, cols) => {
      const list = inG(cats);
      return { title: title, en: en, count: list.length, items: list, gridStyle: 'display: grid; grid-template-columns: repeat(' + cols + ', 112px); gap: 12px' };
    };
    const fieldsTop = [
      field('候选田', 'CANDIDATES', ['candidate'], 6),
      field('已投田', 'APPLIED', ['applied'], 2),
      field('待补证据田', 'NEEDS PROOF', ['incomplete'], 2)
    ];
    const fieldsBottom = [field('归档仓库', 'ARCHIVE', ['closed', 'trash'], 3)];
    const legend = [0, 1, 2, 3, 4, 5].map((k) => ({ crop: CROPS[k], label: STAGE_NAMES[k].split(' ')[0], range: ['0%', '<34%', '<67%', '<100%', '100%', '归档'][k] }));
    const xp = this.xpOf(st);
    const level = Math.floor(xp / 100) + 1;
    const xpIn = xp % 100;
    const xpSegs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((k) => ({ style: 'background: ' + (k < Math.floor(xpIn / 10) ? accent : '#2E2B40') }));
    const live = items.filter((it) => it.stage !== 5);
    const gAll = live.reduce((a, it) => a + it.gaps.length, 0);
    const gDoneAll = live.reduce((a, it) => a + it.gaps.filter((g, k) => st.checks[it.fid + '|g|' + k]).length, 0);
    const qAll = live.reduce((a, it) => a + it.qs.length, 0);
    const qDoneAll = live.reduce((a, it) => a + it.qs.filter((q, k) => st.practiced[it.fid + '|q|' + k]).length, 0);
    const stats = [
      { label: '小镇等级', value: 'Lv.' + level, sub: xp + ' XP 累计', style: 'color: ' + accent },
      { label: '已浇水', value: gDoneAll, sub: '/ ' + gAll + ' 项待核', style: 'color: #8CC4FF' },
      { label: '已施肥', value: qDoneAll, sub: '/ ' + qAll + ' 道预练题', style: 'color: #8FE09C' },
      { label: '开花田块', value: live.filter((it) => it.stage === 4).length, sub: '/ ' + live.length + ' 块在种', style: 'color: #F59AB8' }
    ];
    const dockGroups = GROUPS.map((g) => ({ items: items.filter((it) => g.cats.indexOf(it.cat) >= 0) }));

    const isCard = st.view === 'card';
    return {
      cur: cur,
      tabs: tabs,
      tabLineStyle: measured ? 'left: ' + st.tl.l + 'px; width: ' + st.tl.w + 'px; background: ' + accent : 'width: 0',
      tabElig: st.tab === 'elig',
      tabMatch: st.tab === 'match',
      tabPrep: st.tab === 'prep',
      tabProj: st.tab === 'proj',
      accentFill: 'background: ' + accent + '; color: #1A1405',
      catCounts: catCounts,
      fieldsTop: fieldsTop,
      fieldsBottom: fieldsBottom,
      legend: legend,
      stats: stats,
      level: level,
      xpIn: xpIn,
      xpSegs: xpSegs,
      dockGroups: dockGroups,
      isCard: isCard,
      isOverview: !isCard,
      segCard: isCard ? 'seg is-on' : 'seg',
      segOverview: isCard ? 'seg' : 'seg is-on',
      overviewCls: isCard ? 'dock-item' : 'dock-item is-active',
      soundOn: st.sound,
      soundOff: !st.sound,
      soundPressed: st.sound ? 'true' : 'false',
      soundCls: st.sound ? 'navbtn is-on' : 'navbtn',
      toastMsg: st.toastMsg,
      setCard: this.setCard,
      setAside: this.setAside,
      setPanel: this.setPanel,
      setTabs: this.setTabs,
      setToast: this.setToast,
      setBurst: this.setBurst,
      setRoot: this.setRoot,
      setMain: this.setMain,
      setGrid: this.setGrid,
      setSweep: this.setSweep,
      setFx: this.setFx,
      onPress: this.onPress,
      ringStyle: 'border-color: ' + accent,
      toggleSound: () => {
        const on = !st.sound;
        this.setState({ sound: on }, () => { this.save(); if (on) this.play('chime'); });
        this.toast(on ? '音效已开启' : '音效已关闭');
      },
      showCard: () => this.setState({ view: 'card' }),
      showOverview: () => this.setState({ view: 'overview' }),
      prev: () => { this.play('switch'); this.setState({ sel: (st.sel + CARDS.length - 1) % CARDS.length, view: 'card' }); },
      next: () => { this.play('switch'); this.setState({ sel: (st.sel + 1) % CARDS.length, view: 'card' }); },
      total: CARDS.length
    };
  }
}
