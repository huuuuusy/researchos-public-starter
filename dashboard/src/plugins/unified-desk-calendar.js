/* ResearchOS maintenance header.
 * 中文：Unified Desk 的日历计算；只处理本地日期字符串（YYYY-MM-DD），不读写 DOM 或状态。
 * English: Calendar arithmetic for the Unified Desk; works on local YYYY-MM-DD strings and never touches the DOM or desk state.
 */

(function attachResearchOSUnifiedDeskCalendar(global) {
  "use strict";

  function isoDate(value = new Date()) {
    const date = value instanceof Date ? value : new Date(value);
    if (!Number.isFinite(date.getTime())) return "";
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  }

  // Noon avoids a daylight-saving shift moving the date; a string that does not round-trip (2026-02-30) is rejected.
  function parseIso(value = "") {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value ?? "").trim())) return null;
    const date = new Date(`${value}T12:00:00`);
    return Number.isFinite(date.getTime()) && isoDate(date) === value ? date : null;
  }

  function shiftIso(value = "", offset = 0) {
    const date = parseIso(value);
    if (!date) return "";
    date.setDate(date.getDate() + Number(offset || 0));
    return isoDate(date);
  }

  // Weeks start on Monday; an invalid anchor falls back to today.
  function weekDates(anchor = "") {
    const date = parseIso(anchor) || new Date();
    const mondayOffset = (date.getDay() + 6) % 7;
    date.setDate(date.getDate() - mondayOffset);
    return Array.from({ length: 7 }, (_, index) => shiftIso(isoDate(date), index));
  }

  // Six Monday-first weeks covering the anchor's month.
  function monthDates(anchor = "") {
    const date = parseIso(anchor) || new Date();
    date.setDate(1);
    const first = isoDate(date);
    const start = shiftIso(first, -((date.getDay() + 6) % 7));
    return Array.from({ length: 42 }, (_, index) => shiftIso(start, index));
  }

  function visibleDates(view = "week", anchor = "") {
    if (view === "day") return [anchor];
    if (view === "month") return monthDates(anchor);
    return weekDates(anchor);
  }

  // The anchor one period earlier (direction -1) or later (+1): a calendar month, a week or a day.
  function shiftAnchor(view = "week", anchor = "", direction = 1) {
    if (view === "month") {
      const date = parseIso(anchor) || new Date();
      date.setDate(1);
      date.setMonth(date.getMonth() + direction);
      return isoDate(date);
    }
    return shiftIso(anchor, direction * (view === "week" ? 7 : 1));
  }

  // monthLabel(year, month) formats the month view; day and week views need no wording.
  function periodLabel(view = "week", anchor = "", dates = visibleDates(view, anchor), monthLabel = (year, month) => `${year}-${month}`) {
    if (view === "day") return dates[0];
    if (view === "month") return monthLabel(anchor.slice(0, 4), anchor.slice(5, 7));
    return `${dates[0]} — ${dates[dates.length - 1]}`;
  }

  global.ResearchOSUnifiedDeskCalendar = Object.freeze({
    isoDate,
    monthDates,
    parseIso,
    periodLabel,
    shiftAnchor,
    shiftIso,
    visibleDates,
    weekDates,
  });
})(window);
