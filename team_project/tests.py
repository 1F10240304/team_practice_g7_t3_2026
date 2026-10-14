from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import SeniorProfile, StudentProfile

User = get_user_model()


class StudentMypageTests(TestCase):
    """学生マイページ"""

    def setUp(self):
        self.user = User.objects.create_user(username="student", password="pass")
        StudentProfile.objects.create(user=self.user, name="山田太郎", university="東洋大学 3年")
        self.url = reverse("student_mypage")
        self.data = {
            "name": "山田太郎",
            "university": "東洋大学 3年",
            "introduction": "よろしくお願いします",
            "skills": "スマホの使い方を教えられます",
        }

    def test_ログインしていないとログイン画面へ移動する(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_自分のプロフィールが表示される(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "山田太郎")

    def test_保存するとプロフィールが上書きされる(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {**self.data, "name": "山田花子"})
        self.assertRedirects(response, self.url)
        self.assertEqual(StudentProfile.objects.filter(user=self.user).count(), 1)
        self.assertEqual(StudentProfile.objects.get(user=self.user).name, "山田花子")

    def test_必須項目が空だと保存されない(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {**self.data, "name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StudentProfile.objects.get(user=self.user).name, "山田太郎")

    def test_他のユーザーのプロフィールは表示されない(self):
        other = User.objects.create_user(username="other", password="pass")
        StudentProfile.objects.create(user=other, name="別の学生", university="他大学")
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertNotContains(response, "別の学生")

    def test_高齢者マイページを開くと自分のマイページに戻される(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("senior_mypage"), {"name": "x", "area": "y"}, follow=True)
        self.assertRedirects(response, self.url)
        self.assertFalse(SeniorProfile.objects.filter(user=self.user).exists())


class SeniorMypageTests(TestCase):
    """高齢者マイページ"""

    def setUp(self):
        self.user = User.objects.create_user(username="senior", password="pass")
        SeniorProfile.objects.create(user=self.user, name="佐藤一郎", area="東京都北区")
        self.url = reverse("senior_mypage")
        self.data = {
            "name": "佐藤一郎",
            "area": "東京都北区",
            "introduction": "",
            "needs": "電球の交換",
        }

    def test_ログインしていないとログイン画面へ移動する(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_自分のプロフィールが表示される(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "佐藤一郎")

    def test_保存するとプロフィールが上書きされる(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.data)
        self.assertRedirects(response, self.url)
        self.assertEqual(SeniorProfile.objects.get(user=self.user).needs, "電球の交換")

    def test_必須項目が空だと保存されない(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {**self.data, "area": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SeniorProfile.objects.get(user=self.user).area, "東京都北区")

    def test_学生マイページを開くと自分のマイページに戻される(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("student_mypage"), follow=True)
        self.assertRedirects(response, self.url)
        self.assertFalse(StudentProfile.objects.filter(user=self.user).exists())


class MypageRedirectTests(TestCase):
    """/mypage/ の振り分け"""

    def test_学生は学生マイページへ(self):
        user = User.objects.create_user(username="student", password="pass")
        StudentProfile.objects.create(user=user, name="山田", university="東洋大学")
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("mypage")), reverse("student_mypage"))

    def test_高齢者は高齢者マイページへ(self):
        user = User.objects.create_user(username="senior", password="pass")
        SeniorProfile.objects.create(user=user, name="佐藤", area="北区")
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("mypage")), reverse("senior_mypage"))

    def test_役割がないユーザーは登録画面へ(self):
        user = User.objects.create_user(username="admin", password="pass")
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("mypage")), reverse("select_role"))
        response = self.client.get(reverse("student_mypage"), follow=True)
        self.assertRedirects(response, reverse("select_role"))


class SignupTests(TestCase):
    """新規登録"""

    def test_役割の選択画面が開ける(self):
        response = self.client.get(reverse("select_role"))
        self.assertContains(response, reverse("student_signup"))
        self.assertContains(response, reverse("senior_signup"))

    def test_学生として登録するとログインしてマイページへ(self):
        response = self.client.post(reverse("student_signup"), {
            "username": "taro",
            "password1": "Tsukuba-2026-pass",
            "password2": "Tsukuba-2026-pass",
            "name": "山田太郎",
            "university": "東洋大学 3年",
        }, follow=True)
        self.assertRedirects(response, reverse("student_mypage"))
        self.assertEqual(StudentProfile.objects.get(user__username="taro").name, "山田太郎")
        self.assertTrue(response.context["user"].is_authenticated)

    def test_高齢者として登録するとログインしてマイページへ(self):
        response = self.client.post(reverse("senior_signup"), {
            "username": "ichiro",
            "password1": "Tsukuba-2026-pass",
            "password2": "Tsukuba-2026-pass",
            "name": "佐藤一郎",
            "area": "東京都北区",
        }, follow=True)
        self.assertRedirects(response, reverse("senior_mypage"))
        self.assertEqual(SeniorProfile.objects.get(user__username="ichiro").area, "東京都北区")

    def test_パスワードが一致しないと何も作られない(self):
        response = self.client.post(reverse("student_signup"), {
            "username": "taro",
            "password1": "Tsukuba-2026-pass",
            "password2": "different-pass-99",
            "name": "山田太郎",
            "university": "東洋大学 3年",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="taro").exists())

    def test_プロフィールが空だと何も作られない(self):
        response = self.client.post(reverse("senior_signup"), {
            "username": "ichiro",
            "password1": "Tsukuba-2026-pass",
            "password2": "Tsukuba-2026-pass",
            "name": "",
            "area": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="ichiro").exists())

    def test_ログイン済みで登録画面を開くとマイページへ(self):
        user = User.objects.create_user(username="taro", password="pass")
        StudentProfile.objects.create(user=user, name="山田", university="東洋大学")
        self.client.force_login(user)
        for name in ["select_role", "student_signup", "senior_signup"]:
            self.assertRedirects(self.client.get(reverse(name)), reverse("mypage"),
                                 target_status_code=302)


class LoginLogoutTests(TestCase):
    """ログイン・ログアウト"""

    def setUp(self):
        self.user = User.objects.create_user(username="taro", password="pass")
        StudentProfile.objects.create(user=self.user, name="山田", university="東洋大学")

    def test_ログイン画面から登録画面へ行ける(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, reverse("select_role"))

    def test_ログインするとマイページへ(self):
        response = self.client.post(reverse("login"), {"username": "taro", "password": "pass"},
                                    follow=True)
        self.assertRedirects(response, reverse("student_mypage"))

    def test_パスワードが違うとログインできない(self):
        response = self.client.post(reverse("login"), {"username": "taro", "password": "wrong"})
        self.assertContains(response, "ユーザー名またはパスワードが違います")

    def test_ログアウトするとログイン画面へ(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertRedirects(self.client.get(reverse("student_mypage")),
                             f"{reverse('login')}?next={reverse('student_mypage')}")


class ProfileAdminTests(TestCase):
    """管理画面にプロフィールが出ること"""

    def setUp(self):
        admin_user = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_login(admin_user)

    def test_学生プロフィールの一覧が開ける(self):
        response = self.client.get(reverse("admin:team_project_studentprofile_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_高齢者プロフィールの一覧が開ける(self):
        response = self.client.get(reverse("admin:team_project_seniorprofile_changelist"))
        self.assertEqual(response.status_code, 200)
