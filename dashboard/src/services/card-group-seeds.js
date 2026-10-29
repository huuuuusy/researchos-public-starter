/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「card group seeds」；负责从现有文档生成卡片组合 seed groups。
 * English: Frontend service for card group seeds in the ResearchOS dashboard; owns seed group assembly from existing documents.
 */

(function attachResearchOSCardGroupSeedRules(global) {
  function defaultText(key) {
    return key;
  }

  function normalizeDeps(options = {}) {
    return {
      getDocument: options.getDocument || (() => null),
      inferCardGroupItemType: options.inferCardGroupItemType || (() => "source"),
      normalizeCardGroup: options.normalizeCardGroup || ((group) => group),
      normalizeCardGroupItem: options.normalizeCardGroupItem || ((item) => item),
      resolvePath: options.resolvePath || ((basePath, targetPath) => targetPath || basePath || ""),
      shouldKeepSeedGroup: options.shouldKeepSeedGroup || (() => true),
      text: options.text || defaultText,
    };
  }

  function cardGroupSourceNote(doc = {}) {
    return doc.sensitivity ? `${doc.sensitivity}${doc.status ? ` · ${doc.status}` : ""}` : "";
  }

  function cardGroupItemsFromSourceFiles(doc = {}, options = {}) {
    const deps = normalizeDeps(options);
    return (Array.isArray(doc.source_files) ? doc.source_files : [])
      .map((path) => deps.resolvePath(doc.path, path))
      .filter(Boolean)
      .map((path) => {
        const sourceDoc = deps.getDocument(path);
        return deps.normalizeCardGroupItem(
          {
            type: deps.inferCardGroupItemType(path),
            title: sourceDoc?.title || path,
            path,
            note: deps.text("cardGroupExisting"),
            source: doc.type || "source_file",
          },
          options
        );
      })
      .filter(Boolean);
  }

  function relationshipPatternSeedGroups(documents = [], options = {}) {
    const deps = normalizeDeps(options);
    return (Array.isArray(documents) ? documents : [])
      .filter((doc) => {
        const path = String(doc.path || "");
        return (
          path.startsWith("04_people/relationship_patterns/") &&
          !path.endsWith("/README.md") &&
          (doc.type === "relationship_pattern" || path.endsWith(".md"))
        );
      })
      .map((doc, index) => {
        const peopleItems = (Array.isArray(doc.related_people) ? doc.related_people : [])
          .map((path) => deps.resolvePath(doc.path, path))
          .filter(Boolean)
          .map((path) => {
            const personDoc = deps.getDocument(path);
            return deps.normalizeCardGroupItem(
              {
                type: "person",
                title: personDoc?.title || path,
                path,
                note: deps.text("cardGroupExisting"),
                source: "relationship_pattern",
              },
              options
            );
          })
          .filter(Boolean);
        return deps.normalizeCardGroup(
          {
            id: `relationship-pattern:${doc.path}`,
            title: doc.title || `Relationship Group ${index + 1}`,
            purpose: `已有关系组：${doc.title || doc.path}。处理时先读取源文件，理解人物关系、证据边界和可推进任务；再决定是否补论文卡、项目卡或升级为 M3 跨项目深化。`,
            items: peopleItems,
            group_level: "G1",
            group_kind: "relationship_pattern",
            source_type: "relationship_pattern",
            source_path: doc.path || "",
            source_note: cardGroupSourceNote(doc),
            createdAt: doc.updated || "",
            updatedAt: doc.updated || "",
          },
          index,
          options
        );
      })
      .filter(Boolean);
  }

  function projectSeedGroups(documents = [], options = {}) {
    const deps = normalizeDeps(options);
    return (Array.isArray(documents) ? documents : [])
      .filter((doc) => doc.type === "project" && String(doc.path || "").startsWith("01_knowledge/projects/"))
      .map((doc, index) => deps.normalizeCardGroup(
        {
          id: `project-group:${doc.path}`,
          title: doc.title || `Project Group ${index + 1}`,
          purpose: `G1 项目组：${doc.title || doc.path}。这是由论文、人物和项目源文件组成的基础组合；处理时先判断它回答什么项目问题，再补证据边界、人物角色和下一步行动。`,
          items: cardGroupItemsFromSourceFiles(doc, options),
          group_level: "G1",
          group_kind: "project_group",
          source_type: "project",
          source_path: doc.path || "",
          source_note: cardGroupSourceNote(doc),
          createdAt: doc.updated || "",
          updatedAt: doc.updated || "",
        },
        index,
        options
      ))
      .filter((group) => group && deps.shouldKeepSeedGroup(group));
  }

  function abstractionSeedGroups(documents = [], options = {}) {
    const deps = normalizeDeps(options);
    return (Array.isArray(documents) ? documents : [])
      .filter((doc) => ["project_synthesis", "research_hierarchy"].includes(doc.type) && String(doc.path || "").startsWith("01_knowledge/projects/"))
      .map((doc, index) => deps.normalizeCardGroup(
        {
          id: `abstraction-group:${doc.path}`,
          title: doc.title || `Abstract Group ${index + 1}`,
          purpose: `G2 抽象组：${doc.title || doc.path}。它不是单篇论文或单个合作者，而是从多个 G1 group 中抽象出的研究方向、项目族或观点结构；处理时要说明它如何回到 R 层研究主线。`,
          items: cardGroupItemsFromSourceFiles(doc, options),
          group_level: "G2",
          group_kind: doc.type === "research_hierarchy" ? "research_direction" : "project_synthesis",
          source_type: doc.type,
          source_path: doc.path || "",
          source_note: cardGroupSourceNote(doc),
          createdAt: doc.updated || "",
          updatedAt: doc.updated || "",
        },
        index,
        options
      ))
      .filter(Boolean);
  }

  function seededCardGroups(documents = [], options = {}) {
    return [
      ...relationshipPatternSeedGroups(documents, options),
      ...projectSeedGroups(documents, options),
      ...abstractionSeedGroups(documents, options),
    ];
  }

  global.ResearchOSCardGroupSeedRules = Object.freeze({
    seededCardGroups,
  });
})(typeof window !== "undefined" ? window : globalThis);
