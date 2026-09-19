import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";

type Props = {
  title: string;
  value: string | number;
  description?: string;
  icon: LucideIcon;
};

export default function StatCard({
  title,
  value,
  description,
  icon: Icon,
}: Props) {
  return (
    <Card>
      <CardContent className="p-5">

        <div className="flex items-center justify-between">

          <div>
            <p className="text-sm text-muted-foreground">
              {title}
            </p>

            <p className="mt-2 text-2xl font-bold">
              {value}
            </p>

            {description && (
              <p className="mt-1 text-xs text-muted-foreground">
                {description}
              </p>
            )}
          </div>

          <div className="rounded-lg bg-muted p-3">
            <Icon className="h-5 w-5" />
          </div>

        </div>

      </CardContent>
    </Card>
  );
}