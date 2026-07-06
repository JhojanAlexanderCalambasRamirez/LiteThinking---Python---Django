import { AuthTemplate } from "@/components/templates/AuthTemplate";
import { LoginForm } from "@/components/organisms/LoginForm";

export default function LoginPage() {
  return (
    <AuthTemplate
      title="Iniciar Sesión"
      subtitle="Gestión de empresas y productos"
    >
      <LoginForm />
    </AuthTemplate>
  );
}
