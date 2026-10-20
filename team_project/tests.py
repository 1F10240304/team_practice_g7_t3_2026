from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import HelpRequest, SeniorProfile, StudentProfile

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

    def test_学生として登録するとログインして学生ホームへ(self):
        response = self.client.post(reverse("student_signup"), {
            "username": "taro",
            "password1": "Tsukuba-2026-pass",
            "password2": "Tsukuba-2026-pass",
            "name": "山田太郎",
            "university": "東洋大学 3年",
        }, follow=True)
        self.assertRedirects(response, reverse("student_home"))
        self.assertEqual(StudentProfile.objects.get(user__username="taro").name, "山田太郎")
        self.assertTrue(response.context["user"].is_authenticated)

    def test_高齢者として登録するとログインして高齢者ホームへ(self):
        response = self.client.post(reverse("senior_signup"), {
            "username": "ichiro",
            "password1": "Tsukuba-2026-pass",
            "password2": "Tsukuba-2026-pass",
            "name": "佐藤一郎",
            "area": "東京都北区",
        }, follow=True)
        self.assertRedirects(response, reverse("elderly_home"))
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


class HomeTests(TestCase):
    """ホームの振り分けと、ホーム⇔マイページの移動"""

    def setUp(self):
        self.student = User.objects.create_user(username="student", password="pass")
        StudentProfile.objects.create(user=self.student, name="山田太郎", university="東洋大学")
        self.senior = User.objects.create_user(username="senior", password="pass")
        SeniorProfile.objects.create(user=self.senior, name="佐藤一郎", area="北区")

    def test_学生は学生ホームへ(self):
        self.client.force_login(self.student)
        self.assertRedirects(self.client.get(reverse("home")), reverse("student_home"))

    def test_高齢者は高齢者ホームへ(self):
        self.client.force_login(self.senior)
        self.assertRedirects(self.client.get(reverse("home")), reverse("elderly_home"))

    def test_役割がないユーザーは登録画面へ(self):
        user = User.objects.create_user(username="admin", password="pass")
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("home")), reverse("select_role"))

    def test_ログインしていないと学生ホームは開けない(self):
        url = reverse("student_home")
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_高齢者が学生ホームを開くと自分のホームに戻される(self):
        self.client.force_login(self.senior)
        response = self.client.get(reverse("student_home"), follow=True)
        self.assertRedirects(response, reverse("elderly_home"))

    def test_学生ホームとマイページを行き来できる(self):
        self.client.force_login(self.student)
        home = self.client.get(reverse("student_home"))
        self.assertContains(home, "山田太郎さん")
        self.assertContains(home, f'href="{reverse("student_mypage")}"')
        self.assertContains(self.client.get(reverse("student_mypage")),
                            f'href="{reverse("student_home")}"')

    def test_高齢者ホームとマイページを行き来できる(self):
        self.client.force_login(self.senior)
        self.assertContains(self.client.get(reverse("elderly_home")),
                            f'href="{reverse("senior_mypage")}"')
        self.assertContains(self.client.get(reverse("senior_mypage")),
                            f'href="{reverse("elderly_home")}"')


class StudentHomeRequestTests(TestCase):
    """学生ホームの依頼一覧"""

    def setUp(self):
        user = User.objects.create_user(username="student", password="pass")
        StudentProfile.objects.create(user=user, name="山田", university="東洋大学")
        self.client.force_login(user)
        start = timezone.now()
        end = start + timedelta(hours=1)
        self.setagaya = HelpRequest.objects.create(
            title="電球の交換", area="東京都世田谷区", start_at=start, end_at=end)
        HelpRequest.objects.create(
            title="買い物の付き添い", area="東京都北区", start_at=start, end_at=end)
        HelpRequest.objects.create(
            title="引き受け済みの依頼", area="東京都北区", start_at=start, end_at=end,
            status=HelpRequest.Status.ACCEPTED)

    def test_募集中の依頼だけが表示される(self):
        response = self.client.get(reverse("student_home"))
        self.assertContains(response, "電球の交換")
        self.assertContains(response, "買い物の付き添い")
        self.assertNotContains(response, "引き受け済みの依頼")

    def test_地域で絞り込める(self):
        response = self.client.get(reverse("student_home"), {"area": "世田谷"})
        self.assertContains(response, "電球の交換")
        self.assertNotContains(response, "買い物の付き添い")

    def test_引き受けると学生ホームに戻る(self):
        response = self.client.post(reverse("accept_request", args=[self.setagaya.pk]))
        self.assertRedirects(response, reverse("student_home"))
        self.setagaya.refresh_from_db()
        self.assertEqual(self.setagaya.status, HelpRequest.Status.ACCEPTED)


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


class AcceptRequestTests(TestCase):
    """依頼の引き受け"""

    def setUp(self):
        self.student = User.objects.create_user(username="student", password="pass")
        StudentProfile.objects.create(user=self.student, name="山田", university="東洋大学")
        self.senior = User.objects.create_user(username="senior", password="pass")
        SeniorProfile.objects.create(user=self.senior, name="佐藤", area="北区")
        start = timezone.now()
        self.help_request = HelpRequest.objects.create(
            title="電球の交換", area="東京都世田谷区",
            start_at=start, end_at=start + timedelta(hours=1))
        self.url = reverse("accept_request", args=[self.help_request.pk])

    def test_ログインしていないと引き受けられない(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        self.help_request.refresh_from_db()
        self.assertEqual(self.help_request.status, HelpRequest.Status.OPEN)

    def test_高齢者は引き受けられない(self):
        self.client.force_login(self.senior)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("home"), target_status_code=302)
        self.help_request.refresh_from_db()
        self.assertEqual(self.help_request.status, HelpRequest.Status.OPEN)

    def test_GETでは引き受けられない(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.help_request.refresh_from_db()
        self.assertEqual(self.help_request.status, HelpRequest.Status.OPEN)

    def test_引き受け済みの依頼をもう一度引き受けても変わらない(self):
        self.help_request.status = HelpRequest.Status.ACCEPTED
        self.help_request.save()
        self.client.force_login(self.student)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("student_home"))
        self.help_request.refresh_from_db()
        self.assertEqual(self.help_request.status, HelpRequest.Status.ACCEPTED)

    def test_完了した依頼は募集中に戻らない(self):
        self.help_request.status = HelpRequest.Status.DONE
        self.help_request.save()
        self.client.force_login(self.student)
        self.client.post(self.url)
        self.help_request.refresh_from_db()
        self.assertEqual(self.help_request.status, HelpRequest.Status.DONE)

    def test_存在しない依頼は404(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("accept_request", args=[9999]))
        self.assertEqual(response.status_code, 404)
