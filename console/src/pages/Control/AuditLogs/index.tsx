import { useCallback, useEffect, useState } from "react";
import { Button, Card, Select, Table, Tag } from "@agentscope-ai/design";
import type { ColumnsType } from "antd/es/table";
import { useTranslation } from "react-i18next";
import api from "../../../api";
import type { AuditEntry } from "../../../api/modules/audit";
import styles from "./index.module.less";

const ACTION_COLORS: Record<string, string> = {
  tool_call: "blue",
  approval_decision: "orange",
  config_change: "purple",
  skill_change: "green",
  mcp_change: "cyan",
  cron_change: "geekblue",
};

const RESULT_COLORS: Record<string, string> = {
  success: "green",
  denied: "red",
  error: "red",
  timeout: "orange",
  approved: "green",
};

const PAGE_SIZE = 20;

function AuditLogsPage() {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState<string | undefined>();

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.listAuditEntries({
        action: actionFilter,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      });
      setEntries(res.entries);
      setTotal(res.total);
    } catch (err) {
      console.error("Failed to fetch audit entries:", err);
    } finally {
      setLoading(false);
    }
  }, [page, actionFilter]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  const columns: ColumnsType<AuditEntry> = [
    {
      title: t("audit.time"),
      dataIndex: "timestamp",
      key: "timestamp",
      width: 180,
      render: (ts: number) =>
        new Date(ts * 1000).toLocaleString(),
    },
    {
      title: t("audit.actor"),
      dataIndex: "actor",
      key: "actor",
      width: 100,
    },
    {
      title: t("audit.action"),
      dataIndex: "action",
      key: "action",
      width: 160,
      render: (action: string) => (
        <Tag color={ACTION_COLORS[action] || "default"}>
          {t(`audit.actions.${action}`, action)}
        </Tag>
      ),
    },
    {
      title: t("audit.target"),
      dataIndex: "target",
      key: "target",
      width: 200,
      ellipsis: true,
    },
    {
      title: t("audit.summary"),
      dataIndex: "summary",
      key: "summary",
      ellipsis: true,
    },
    {
      title: t("audit.result"),
      dataIndex: "result",
      key: "result",
      width: 100,
      render: (result: string) => (
        <Tag color={RESULT_COLORS[result] || "default"}>{result}</Tag>
      ),
    },
  ];

  return (
    <div className={styles.auditLogsPage}>
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <h1 className={styles.title}>{t("audit.title")}</h1>
          <p className={styles.description}>{t("audit.description")}</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Select
            allowClear
            placeholder={t("audit.filterAction")}
            style={{ width: 180 }}
            value={actionFilter}
            onChange={(val) => {
              setActionFilter(val);
              setPage(1);
            }}
            options={[
              { label: t("audit.actions.tool_call"), value: "tool_call" },
              { label: t("audit.actions.approval_decision"), value: "approval_decision" },
              { label: t("audit.actions.config_change"), value: "config_change" },
              { label: t("audit.actions.skill_change"), value: "skill_change" },
              { label: t("audit.actions.mcp_change"), value: "mcp_change" },
              { label: t("audit.actions.cron_change"), value: "cron_change" },
            ]}
          />
          <Button onClick={fetchEntries}>{t("common.refresh")}</Button>
        </div>
      </div>

      <Card className={styles.tableCard} bodyStyle={{ padding: 0 }}>
        <Table
          columns={columns}
          dataSource={entries}
          loading={loading}
          rowKey="id"
          pagination={{
            current: page,
            pageSize: PAGE_SIZE,
            total,
            showSizeChanger: false,
            onChange: (p) => setPage(p),
            showTotal: (t) => `${t} items`,
          }}
        />
      </Card>
    </div>
  );
}

export default AuditLogsPage;
