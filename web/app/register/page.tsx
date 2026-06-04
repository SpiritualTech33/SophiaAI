import SiteHeader from "@/components/layout/SiteHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import AuthCard from "@/components/auth/AuthCard";

export const metadata = { title: "Enter the Portal — SophiaAI" };

export default function RegisterPage() {
  return (
    <>
      <SiteHeader />
      <main className="site-main">
        <AuthCard mode="register" />
      </main>
      <SiteFooter />
    </>
  );
}
