/* 岗位小镇 · 离线渲染器
 * 读取 <template id="dc-template"> 里的界面模板，支持 {{路径}}、<sc-for>、<sc-if>、
 * onClick / onPointerDown 事件和 ref 回调；状态变化后按位置比对并更新 DOM。
 * 不联网、无第三方依赖，供双击打开的 dashboard.html 使用。 */
(function () {
  'use strict';
  var HOLE = /\{\{\s*([^}]+?)\s*\}\}/g;
  var WHOLE = /^\{\{\s*([^}]+?)\s*\}\}$/;
  var EVENTS = { onclick: 'click', onpointerdown: 'pointerdown' };

  function lookup(path, scope) {
    if (path === 'true') return true;
    if (path === 'false') return false;
    if (/^-?\d+(\.\d+)?$/.test(path)) return Number(path);
    var parts = path.split('.');
    for (var s = scope; s; s = s.__parent) {
      if (Object.prototype.hasOwnProperty.call(s, parts[0])) {
        var v = s[parts[0]];
        for (var i = 1; i < parts.length && v != null; i++) v = v[parts[i]];
        return v;
      }
    }
    return undefined;
  }
  function text(str, scope) {
    return str.replace(HOLE, function (_, p) { var v = lookup(p, scope); return v == null ? '' : String(v); });
  }
  function raw(str, scope) {
    var m = WHOLE.exec(str);
    return m ? lookup(m[1], scope) : text(str, scope);
  }

  // 模板 DOM -> 虚拟节点
  function build(nodes, scope, out) {
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (n.nodeType === 3) {
        if (/^\s*$/.test(n.data)) continue;
        out.push({ t: text(n.data, scope) });
        continue;
      }
      if (n.nodeType !== 1) continue;
      var tag = n.localName;
      if (tag === 'sc-for') {
        var list = raw(n.getAttribute('list') || '', scope) || [];
        var as = n.getAttribute('as') || 'item';
        for (var k = 0; k < list.length; k++) {
          var child = { __parent: scope, $index: k };
          child[as] = list[k];
          build(n.childNodes, child, out);
        }
        continue;
      }
      if (tag === 'sc-if') {
        if (raw(n.getAttribute('value') || '', scope)) build(n.childNodes, scope, out);
        continue;
      }
      var v = { tag: tag, ns: n.namespaceURI, attrs: {}, on: {}, ref: null, kids: [] };
      for (var a = 0; a < n.attributes.length; a++) {
        var at = n.attributes[a];
        var name = at.name;
        if (name.indexOf('hint-') === 0) continue;
        if (EVENTS[name.toLowerCase()]) { v.on[EVENTS[name.toLowerCase()]] = raw(at.value, scope); continue; }
        if (name === 'ref') { v.ref = raw(at.value, scope); continue; }
        var val = raw(at.value, scope);
        if (val === undefined || val === null || val === false) continue;
        v.attrs[name] = String(val);
      }
      build(n.childNodes, scope, v.kids);
      out.push(v);
    }
    return out;
  }

  var refs = [];
  function create(v) {
    if (v.t !== undefined) return document.createTextNode(v.t);
    var el = v.ns && v.ns !== 'http://www.w3.org/1999/xhtml' ? document.createElementNS(v.ns, v.tag) : document.createElement(v.tag);
    update(el, v);
    return el;
  }
  function update(el, v) {
    var old = el.__attrs || {};
    for (var k in old) if (!(k in v.attrs)) el.removeAttribute(k);
    for (var k2 in v.attrs) if (old[k2] !== v.attrs[k2]) el.setAttribute(k2, v.attrs[k2]);
    el.__attrs = v.attrs;
    el.__on = el.__on || {};
    for (var type in v.on) {
      if (!(type in el.__on)) {
        (function (t) { el.addEventListener(t, function (e) { var h = el.__on[t]; if (typeof h === 'function') h(e); }); })(type);
      }
      el.__on[type] = v.on[type];
    }
    if (typeof v.ref === 'function') refs.push([v.ref, el]);
    patch(el, v.kids);
  }
  function patch(parent, kids) {
    for (var i = 0; i < kids.length; i++) {
      var v = kids[i];
      var cur = parent.childNodes[i];
      if (v.t !== undefined) {
        if (cur && cur.nodeType === 3) { if (cur.data !== v.t) cur.data = v.t; }
        else if (cur) parent.replaceChild(create(v), cur);
        else parent.appendChild(create(v));
        continue;
      }
      if (cur && cur.nodeType === 1 && cur.localName === v.tag && cur.namespaceURI === (v.ns || cur.namespaceURI)) update(cur, v);
      else if (cur) parent.replaceChild(create(v), cur);
      else parent.appendChild(create(v));
    }
    while (parent.childNodes.length > kids.length) parent.removeChild(parent.lastChild);
  }

  window.DCLogic = function DCLogic() {};
  window.DCLogic.prototype.setState = function (partial, cb) {
    var prev = this.state;
    this.state = Object.assign({}, prev, typeof partial === 'function' ? partial(prev, this.props) : partial);
    this.__render();
    if (this.componentDidUpdate) this.componentDidUpdate(this.props, prev);
    if (cb) cb();
  };
  window.DCLogic.prototype.forceUpdate = function (cb) { this.setState({}, cb); };

  window.DCMount = function (Component, host, tpl, props) {
    var c = new Component();
    c.props = props || {};
    c.state = c.state || {};
    var nodes = tpl.content.childNodes;
    c.__render = function () {
      refs = [];
      patch(host, build(nodes, c.renderVals(), []));
      refs.forEach(function (r) { r[0](r[1]); });
    };
    c.__render();
    if (c.componentDidMount) c.componentDidMount();
    return c;
  };
})();
