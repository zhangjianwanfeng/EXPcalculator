(() => {
  'use strict';

  /* ---------------------------- Helpers & State ---------------------------- */
  const $ = (selector) => document.querySelector(selector);
  const levelExpTable = Object.create(null);
  let finishAt = null;
  let cdTimer = null;

  /* ----------------------------- DOM Elements ------------------------------ */
  const dom = {
    form: $('#expForm'),
    cur: $('#currentLevel'),
    curExp: $('#currentExp'),
    tgt: $('#targetLevel'),
    eph: $('#expPerHour'),
    dailyAccel: $('#dailyAccel'),
    stoneAccel: $('#stoneAccel'),
    calcBtn: $('#calcBtn'),
    results: $('#results'),
    remaining: $('#remainingExp'),
    needSecs: $('#neededSeconds'),
    accelInfo: $('#accelInfo'),
    now: $('#nowTime'),
    finish: $('#finishTime'),
    cd: $('#countdown'),
    counter: $('#counter'),
    todayCounter: $('#todayCounter'),
  };

  /* --------------------------------- Init ---------------------------------- */
  (async function init() {
    try {
      await loadCsv('1.csv');
      dom.calcBtn.disabled = false;
    } catch (err) {
      console.error('初始化失败:', err);
      alert('初始化失败: ' + (err.message || err));
    }

    bindEvents();
    fetchCounters();
  })();

  /* ----------------------------- Event Binding ----------------------------- */
  function bindEvents() {
    dom.form.addEventListener('submit', (e) => {
      e.preventDefault();
      calculate();
    });
  }

  /* ------------------------------ CSV Helpers ------------------------------ */
  async function loadCsv(url) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error('CSV 加载失败: ' + res.status);
      parseCsv(await res.text());
    } catch (err) {
      throw new Error('无法加载经验数据: ' + err.message);
    }
  }

  function parseCsv(text) {
    try {
      const lines = text.trim().split(/\r?\n/);
      if (lines.length < 2) throw new Error('CSV格式错误');
      
      lines.slice(1).forEach((line, index) => {
        const [lv, exp] = line.split(',');
        if (!lv || !exp) {
          console.warn(`跳过无效行 ${index + 2}: ${line}`);
          return;
        }
        const level = Number(lv);
        const experience = Number(exp);
        if (isNaN(level) || isNaN(experience)) {
          console.warn(`跳过无效数据行 ${index + 2}: ${line}`);
          return;
        }
        levelExpTable[level] = experience;
      });
      
      if (Object.keys(levelExpTable).length === 0) {
        throw new Error('没有有效的等级经验数据');
      }
      
      console.log(`成功加载 ${Object.keys(levelExpTable).length} 个等级的经验数据`);
    } catch (err) {
      throw new Error('解析CSV失败: ' + err.message);
    }
  }

  /* ----------------------------- Core Features ----------------------------- */
  function calculate() {
    try {
      const cur = Number(dom.cur.value);
      const curExp = Number(dom.curExp.value);
      const tgt = Number(dom.tgt.value);
      const rate = Number(dom.eph.value);
      const dailyAccel = Number(dom.dailyAccel.value) || 0;
      const stoneAccel = Number(dom.stoneAccel.value) || 0;

      if (!cur || !tgt || !rate) {
        alert('请输入完整数据');
        return;
      }
      
      if (curExp < 0) {
        alert('现有经验不能为负数');
        return;
      }
      
      if (tgt <= cur) {
        alert('目标等级必须高于当前等级');
        return;
      }

      if (dailyAccel < 0 || dailyAccel > 10) {
        alert('日常加速次数应在0-10之间');
        return;
      }

      if (stoneAccel < 0 || stoneAccel > 50) {
        alert('加速石头次数应在0-50之间');
        return;
      }

      let need = 0;
      for (let lv = cur; lv < tgt; lv++) {
        const exp = levelExpTable[lv];
        if (exp == null) {
          alert(`等级 ${lv} 经验缺失，请检查经验表数据`);
          return;
        }
        need += exp;
      }

      need -= curExp;
      if (need <= 0) {
        alert('已达到目标等级');
        return;
      }

      // 计算加速效果 - 减少2小时所需经验值
      const baseSeconds = need / (rate / 3600);
      let finalSeconds = baseSeconds;
      let accelInfo = '';

      if (dailyAccel > 0 || stoneAccel > 0) {
        // 每小时经验值
        const expPerHour = rate;
        // 2小时所需经验值
        const expPer2Hours = expPerHour * 2;
        
        // 日常加速：每次减少2小时经验值
        const dailyReduction = dailyAccel * expPer2Hours;
        // 加速石头：每次减少2小时经验值
        const stoneReduction = stoneAccel * expPer2Hours;
        const totalReduction = dailyReduction + stoneReduction;
        
        // 减少所需经验值
        const reducedNeed = Math.max(0, need - totalReduction);
        
        if (reducedNeed <= 0) {
          finalSeconds = 0;
          accelInfo = `加速效果: 立即完成 (日常加速${dailyAccel}次, 加速石头${stoneAccel}次, 共减少${totalReduction.toLocaleString()}经验)`;
        } else {
          finalSeconds = reducedNeed / (rate / 3600);
          accelInfo = `加速效果: 减少${totalReduction.toLocaleString()}经验 (日常加速${dailyAccel}次, 加速石头${stoneAccel}次)`;
        }
      }

      if (!isFinite(finalSeconds) || finalSeconds < 0) {
        alert('计算错误，请检查输入数据');
        return;
      }
      
      showResult(need, finalSeconds, accelInfo);
    } catch (err) {
      console.error('计算错误:', err);
      alert('计算过程中出现错误: ' + err.message);
    }
  }

  function showResult(need, seconds, accelInfo = '') {
    dom.results.hidden = false;
    dom.remaining.textContent = `剩余经验值: ${need.toLocaleString()}`;
    
    if (accelInfo) {
      dom.accelInfo.textContent = accelInfo;
      dom.accelInfo.hidden = false;
    } else {
      dom.accelInfo.hidden = true;
    }

    const now = new Date();
    finishAt = new Date(now.getTime() + seconds * 1000);

    dom.now.textContent = `现在时间: ${now.toLocaleString()}`;
    dom.finish.textContent = `完成时间: ${finishAt.toLocaleString()}`;

    clearInterval(cdTimer);
    tick();
    cdTimer = setInterval(tick, 1000);
  }

  function tick() {
    if (!finishAt) return;
    
    const diff = finishAt - Date.now();
    if (diff <= 0) {
      dom.cd.textContent = '倒计时: 已完成!';
      return clearInterval(cdTimer);
    }

    const s = Math.ceil(diff / 1000);
    const hours = Math.floor(s / 3600);
    const minutes = Math.floor((s % 3600) / 60);
    const seconds = s % 60;
    dom.cd.textContent = `倒计时: ${hours}h ${minutes}m ${seconds}s`;
  }

  /* ----------------------------- Visit Counter ----------------------------- */
  async function fetchCounters() {
    try {
      const [totalCount, todayCount] = await Promise.all([
        getText('/visit-count'),
        getText('/visit-count-today')
      ]);
      dom.counter.textContent = totalCount;
      dom.todayCounter.textContent = todayCount;
    } catch (err) {
      console.error('获取访问统计失败:', err);
      dom.counter.textContent = '读取失败';
      dom.todayCounter.textContent = '读取失败';
    }
  }

  async function getText(url) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return await res.text();
    } catch (err) {
      throw new Error('请求失败: ' + err.message);
    }
  }
})();