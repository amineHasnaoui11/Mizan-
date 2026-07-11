import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { Card, CardBody } from "@/components/ui/Card";

export function StatCard({
  label,
  value,
  suffix,
  icon: Icon,
  delay = 0,
}: {
  label: string;
  value: string | number;
  suffix?: string;
  icon: LucideIcon;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -3 }}
    >
      <Card className="hover:shadow-lift">
        <CardBody className="flex items-center gap-4">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-ink/8 text-ink">
            <Icon size={20} strokeWidth={2} />
          </div>
          <div>
            <div className="font-mono text-2xl font-semibold text-ink">
              {value}
              {suffix && <span className="text-base text-muted"> {suffix}</span>}
            </div>
            <div className="text-xs text-muted">{label}</div>
          </div>
        </CardBody>
      </Card>
    </motion.div>
  );
}
