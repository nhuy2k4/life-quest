import { Input } from '@/components/ui/input';

export function TextArea(props: React.ComponentProps<typeof Input>) {
  return <Input multiline numberOfLines={4} textAlignVertical="top" {...props} />;
}
