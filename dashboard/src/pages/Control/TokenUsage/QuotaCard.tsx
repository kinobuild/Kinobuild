/**
 * Quota card — the account's lifetime token allowance plus voucher redemption.
 *
 * Users may hold a role without the admin ``users`` permission, so the voucher
 * generator only renders for admins (`role === "admin"`), matching the backend
 * ``require_permission("users")`` gate on ``POST /api/quota-codes``.
 */

import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Input,
  InputNumber,
  Progress,
  Space,
  Table,
  Tag,
  Typography,
} from "antd";
import CopyOutlined from "@ant-design/icons/CopyOutlined";
import { useTranslation } from "react-i18next";
import i18n from "../../../i18n";
import { useUserRole } from "../../../hooks/useUserRole";
import { request } from "../../../api/request";
import { message } from "../../../utils/antdMessage";
import { formatCompactCount } from "./formatUsageCount";
import styles from "./index.module.less";

const { Text } = Typography;

type QuotaState = {
  token_quota: number | null;
  quota_used: number;
  quota_remaining: number | null;
};

type VoucherRow = {
  code: string;
  tokens: number;
  note: string;
  status: "unused" | "redeemed" | "revoked";
  redeemed_at: number | null;
};

export function QuotaCard() {
  const { t } = useTranslation();
  const locale = i18n.language?.startsWith("zh") ? "zh" : "en";
  const role = useUserRole();
  const isAdmin = role === "admin";
  const [quota, setQuota] = useState<QuotaState | null>(null);
  const [code, setCode] = useState("");
  const [redeeming, setRedeeming] = useState(false);
  const [genCount, setGenCount] = useState(10);
  const [genTokens, setGenTokens] = useState(3_000_000);
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState<VoucherRow[]>([]);
  const [recent, setRecent] = useState<VoucherRow[]>([]);

  const loadQuota = useCallback(async () => {
    try {
      const data = await request<QuotaState>("/quota-codes");
      setQuota(data);
    } catch {
      setQuota(null);
    }
  }, []);

  const loadRecent = useCallback(async () => {
    if (!isAdmin) return;
    try {
      const data = await request<{ codes: VoucherRow[] }>(
        "/quota-codes/codes?limit=20",
      );
      setRecent(data.codes || []);
    } catch {
      setRecent([]);
    }
  }, [isAdmin]);

  useEffect(() => {
    void loadQuota();
    void loadRecent();
  }, [loadQuota, loadRecent]);

  const redeem = async () => {
    const value = code.trim();
    if (!value) return;
    setRedeeming(true);
    try {
      const result = await request<{
        token_quota: number;
        quota_remaining: number;
      }>("/quota-codes/redeem", {
        method: "POST",
        body: JSON.stringify({ code: value }),
      });
      message.success(
        t("usage.quota.redeemOk", {
          n: formatCompactCount(result.token_quota, locale),
        }),
      );
      setCode("");
      await Promise.all([loadQuota(), loadRecent()]);
    } catch (error) {
      const text = error instanceof Error ? error.message : String(error);
      message.error(text || t("usage.quota.redeemFailed"));
    } finally {
      setRedeeming(false);
    }
  };

  const generate = async () => {
    setGenerating(true);
    try {
      const result = await request<{ codes: VoucherRow[] }>("/quota-codes", {
        method: "POST",
        body: JSON.stringify({ count: genCount, tokens: genTokens, note: "" }),
      });
      setGenerated(result.codes || []);
      message.success(
        t("usage.quota.generateOk", { n: (result.codes || []).length }),
      );
      await loadRecent();
    } catch (error) {
      const text = error instanceof Error ? error.message : String(error);
      message.error(text || t("usage.quota.generateFailed"));
    } finally {
      setGenerating(false);
    }
  };

  const copyCodes = async () => {
    const text = generated.map((row) => row.code).join("\n");
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      message.success(t("usage.quota.copied"));
    } catch {
      message.error(t("usage.quota.copyFailed"));
    }
  };

  const quotaTotal = quota?.token_quota ?? null;
  const used = quota?.quota_used ?? 0;
  const remaining = quota?.quota_remaining ?? null;
  const percent =
    quotaTotal && quotaTotal > 0
      ? Math.min(100, Math.round((used / quotaTotal) * 100))
      : 100;

  const columns = [
    {
      title: t("usage.quota.colCode"),
      dataIndex: "code",
      key: "code",
      render: (value: string) => <Text code>{value}</Text>,
    },
    {
      title: t("usage.quota.colTokens"),
      dataIndex: "tokens",
      key: "tokens",
      render: (value: number) => formatCompactCount(value, locale),
    },
    {
      title: t("usage.quota.colStatus"),
      dataIndex: "status",
      key: "status",
      render: (value: string) => (
        <Tag
          color={
            value === "unused"
              ? "green"
              : value === "redeemed"
              ? "blue"
              : "default"
          }
        >
          {t(`usage.quota.status.${value}`)}
        </Tag>
      ),
    },
  ];

  return (
    <Card
      className={styles.quotaCard}
      title={t("usage.quota.title")}
      size="small"
    >
      {quotaTotal === null ? (
        <Alert type="info" showIcon message={t("usage.quota.unlimited")} />
      ) : (
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <Progress
            percent={percent}
            status={percent >= 100 ? "exception" : "normal"}
            format={() => `${percent}%`}
          />
          <Space size="large" wrap>
            <Text>
              {t("usage.quota.used")}:{" "}
              <Text strong>{formatCompactCount(used, locale)}</Text>
            </Text>
            <Text>
              {t("usage.quota.total")}:{" "}
              <Text strong>{formatCompactCount(quotaTotal, locale)}</Text>
            </Text>
            <Text>
              {t("usage.quota.remaining")}:{" "}
              <Text strong type={remaining === 0 ? "danger" : "success"}>
                {formatCompactCount(remaining ?? 0, locale)}
              </Text>
            </Text>
          </Space>
          {remaining === 0 ? (
            <Alert
              type="warning"
              showIcon
              message={t("usage.quota.exhausted")}
            />
          ) : null}
        </Space>
      )}

      <Space.Compact style={{ width: "100%", marginTop: 16 }}>
        <Input
          value={code}
          onChange={(event) => setCode(event.target.value)}
          placeholder={t("usage.quota.codePlaceholder")}
          onPressEnter={() => void redeem()}
        />
        <Button
          type="primary"
          loading={redeeming}
          onClick={() => void redeem()}
        >
          {t("usage.quota.redeem")}
        </Button>
      </Space.Compact>

      {isAdmin ? (
        <div style={{ marginTop: 20 }}>
          <Text strong>{t("usage.quota.adminTitle")}</Text>
          <Space wrap style={{ marginTop: 8 }}>
            <InputNumber
              min={1}
              max={200}
              value={genCount}
              onChange={(value) => setGenCount(Number(value) || 1)}
              addonBefore={t("usage.quota.count")}
            />
            <InputNumber
              min={10_000}
              step={100_000}
              value={genTokens}
              onChange={(value) => setGenTokens(Number(value) || 100_000)}
              addonBefore={t("usage.quota.tokensEach")}
              style={{ width: 260 }}
            />
            <Button
              type="primary"
              loading={generating}
              onClick={() => void generate()}
            >
              {t("usage.quota.generate")}
            </Button>
            {generated.length ? (
              <Button icon={<CopyOutlined />} onClick={() => void copyCodes()}>
                {t("usage.quota.copyAll")}
              </Button>
            ) : null}
          </Space>
          {generated.length ? (
            <Table
              style={{ marginTop: 12 }}
              size="small"
              rowKey="code"
              pagination={false}
              columns={columns}
              dataSource={generated}
            />
          ) : null}
          {recent.length ? (
            <>
              <Text
                type="secondary"
                style={{ display: "block", marginTop: 12 }}
              >
                {t("usage.quota.recent")}
              </Text>
              <Table
                size="small"
                rowKey="code"
                pagination={false}
                columns={columns}
                dataSource={recent}
              />
            </>
          ) : null}
        </div>
      ) : null}
    </Card>
  );
}
