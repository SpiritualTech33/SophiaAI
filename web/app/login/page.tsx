import SiteHeader from "@/components/layout/SiteHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import AuthCard from "@/components/auth/AuthCard";

export const metadata = { title: "Sign in — SophiaAI" };

export default function LoginPage() {
  return (
    <>
      <SiteHeader />
      <main className="site-main">
        <AuthCard mode="login" />
      </main>
      <SiteFooter />
    </>
  );
}
