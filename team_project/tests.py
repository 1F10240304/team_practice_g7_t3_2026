from datetime import date, time, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import HelpRequest, SeniorProfile, StudentProfile, TalkTheme
from .views import _schedule_from_text

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

    def test_高齢者のマイページから一覧へ行ける(self):
        self.client.force_login(self.senior)
        self.assertContains(self.client.get(reverse("senior_mypage")),
                            f'href="{reverse("my_requests")}"')


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

    def test_学生がログインすると学生ホームへ(self):
        response = self.client.post(reverse("login"), {"username": "taro", "password": "pass"},
                                    follow=True)
        self.assertRedirects(response, reverse("student_home"))

    def test_高齢者がログインすると高齢者ホームへ(self):
        senior = User.objects.create_user(username="ichiro", password="pass")
        SeniorProfile.objects.create(user=senior, name="佐藤", area="北区")
        response = self.client.post(reverse("login"), {"username": "ichiro", "password": "pass"},
                                    follow=True)
        self.assertRedirects(response, reverse("elderly_home"))

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


class HelpRequestAdminTests(TestCase):
    """管理画面で依頼を見られること"""

    def setUp(self):
        admin_user = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_login(admin_user)
        start = timezone.now()
        end = start + timedelta(hours=1)
        HelpRequest.objects.create(
            title="電球の交換", area="東京都世田谷区", start_at=start, end_at=end)
        HelpRequest.objects.create(
            title="買い物の付き添い", area="東京都北区", start_at=start, end_at=end,
            status=HelpRequest.Status.ACCEPTED)
        self.url = reverse("admin:team_project_helprequest_changelist")

    def test_依頼の一覧が開ける(self):
        response = self.client.get(self.url)
        self.assertContains(response, "電球の交換")
        self.assertContains(response, "買い物の付き添い")

    def test_状態で絞り込める(self):
        response = self.client.get(self.url, {"status__exact": "accepted"})
        self.assertContains(response, "買い物の付き添い")
        self.assertNotContains(response, "電球の交換")

    def test_地域で検索できる(self):
        response = self.client.get(self.url, {"q": "世田谷"})
        self.assertContains(response, "電球の交換")
        self.assertNotContains(response, "買い物の付き添い")


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


class HelpRequestHelperTests(TestCase):
    """依頼を引き受けた学生（helper）"""

    def setUp(self):
        self.student = User.objects.create_user(username="student", password="pass")
        start = timezone.now()
        self.help_request = HelpRequest.objects.create(
            title="電球の交換", area="東京都世田谷区",
            start_at=start, end_at=start + timedelta(hours=1))

    def test_作ったばかりの依頼は引き受けた学生が空(self):
        self.assertIsNone(self.help_request.helper)

    def test_引き受けた学生を記録して学生側からたどれる(self):
        self.help_request.helper = self.student
        self.help_request.save()
        self.assertEqual(list(self.student.helped_requests.all()), [self.help_request])

    def test_学生のアカウントが消えても依頼は残る(self):
        self.help_request.helper = self.student
        self.help_request.save()
        self.student.delete()
        self.help_request.refresh_from_db()
        self.assertIsNone(self.help_request.helper)


class StudentAcceptedRequestsTests(TestCase):
    """引き受けた学生の記録と、引き受けた依頼の一覧"""

    def setUp(self):
        self.student = User.objects.create_user(username="student", password="pass")
        StudentProfile.objects.create(user=self.student, name="山田", university="東洋大学")
        self.other = User.objects.create_user(username="other", password="pass")
        StudentProfile.objects.create(user=self.other, name="鈴木", university="他大学")
        self.senior = User.objects.create_user(username="senior", password="pass")
        SeniorProfile.objects.create(user=self.senior, name="佐藤", area="北区")
        start = timezone.now()
        end = start + timedelta(hours=1)
        self.open_request = HelpRequest.objects.create(
            title="電球の交換", area="東京都世田谷区", start_at=start, end_at=end)
        self.mine = HelpRequest.objects.create(
            title="買い物の付き添い", area="東京都北区", start_at=start, end_at=end,
            status=HelpRequest.Status.ACCEPTED, helper=self.student)
        self.mine_done = HelpRequest.objects.create(
            title="庭の草むしり", area="東京都北区", start_at=start, end_at=end,
            status=HelpRequest.Status.DONE, helper=self.student)
        HelpRequest.objects.create(
            title="他の学生の依頼", area="東京都北区", start_at=start, end_at=end,
            status=HelpRequest.Status.ACCEPTED, helper=self.other)
        self.url = reverse("student_accepted_requests")

    def test_引き受けると自分がhelperとして記録される(self):
        self.client.force_login(self.student)
        self.client.post(reverse("accept_request", args=[self.open_request.pk]))
        self.open_request.refresh_from_db()
        self.assertEqual(self.open_request.helper, self.student)

    def test_引き受け済みの依頼のhelperは書き換わらない(self):
        self.client.force_login(self.other)
        self.client.post(reverse("accept_request", args=[self.mine.pk]))
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.helper, self.student)

    def test_自分が引き受けた依頼だけが表示される(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url)
        self.assertContains(response, "買い物の付き添い")
        self.assertContains(response, "庭の草むしり")
        self.assertNotContains(response, "他の学生の依頼")
        self.assertNotContains(response, "電球の交換")

    def test_引き受け済みと完了に分かれる(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["accepted_requests"]), [self.mine])
        self.assertEqual(list(response.context["done_requests"]), [self.mine_done])

    def test_引き受けた依頼が一覧に出る(self):
        self.client.force_login(self.student)
        self.client.post(reverse("accept_request", args=[self.open_request.pk]))
        self.assertContains(self.client.get(self.url), "電球の交換")

    def test_ログインしていないと開けない(self):
        self.assertRedirects(self.client.get(self.url), f"{reverse('login')}?next={self.url}")

    def test_高齢者が開くと自分のホームに戻される(self):
        self.client.force_login(self.senior)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse("elderly_home"))


class CompleteRequestTests(TestCase):
    """依頼の完了とトークテーマ"""

    def setUp(self):
        self.student = User.objects.create_user(username="student", password="pass")
        StudentProfile.objects.create(user=self.student, name="山田", university="東洋大学")
        self.other = User.objects.create_user(username="other", password="pass")
        StudentProfile.objects.create(user=self.other, name="鈴木", university="他大学")
        start = timezone.now()
        end = start + timedelta(hours=1)
        self.help_request = HelpRequest.objects.create(
            title="電球の交換をお願いしたいです", area="東京都北区", start_at=start, end_at=end,
            status=HelpRequest.Status.ACCEPTED, helper=self.student)
        self.open_request = HelpRequest.objects.create(
            title="買い物をお願いしたいです", area="東京都北区", start_at=start, end_at=end)
        self.url = reverse("complete_request", args=[self.help_request.pk])

    def test_完了にすると状態が完了になり一覧に戻る(self):
        self.client.force_login(self.student)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("student_accepted_requests"))
        self.help_request.refresh_from_db()
        self.assertEqual(self.help_request.status, HelpRequest.Status.DONE)

    def test_完了にするとトークテーマが作られ一覧に表示される(self):
        self.client.force_login(self.student)
        self.client.post(self.url)
        theme = TalkTheme.objects.get(help_request=self.help_request)
        self.assertIn("明かり", theme.text)
        self.assertContains(self.client.get(reverse("student_accepted_requests")), theme.text)

    def test_AIの関数があればその文章を使う(self):
        self.client.force_login(self.student)
        with mock.patch("team_project.ai.generate_talk_theme", create=True,
                        return_value="好きな季節の話"):
            self.client.post(self.url)
        self.assertEqual(self.help_request.talk_theme.text, "好きな季節の話")

    def test_AIが失敗しても完了になる(self):
        self.client.force_login(self.student)
        with mock.patch("team_project.ai.generate_talk_theme", create=True,
                        side_effect=RuntimeError("通信エラー")):
            self.client.post(self.url)
        self.help_request.refresh_from_db()
        self.assertEqual(self.help_request.status, HelpRequest.Status.DONE)
        self.assertTrue(self.help_request.talk_theme.text)

    def test_他の学生が引き受けた依頼は完了にできない(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.help_request.refresh_from_db()
        self.assertEqual(self.help_request.status, HelpRequest.Status.ACCEPTED)

    def test_募集中の依頼は完了にできない(self):
        self.client.force_login(self.student)
        url = reverse("complete_request", args=[self.open_request.pk])
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_完了した依頼をもう一度完了にしてもトークテーマは1つだけ(self):
        self.client.force_login(self.student)
        self.client.post(self.url)
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.assertEqual(TalkTheme.objects.filter(help_request=self.help_request).count(), 1)

    def test_ログインしていないと完了にできない(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_GETでは完了にできない(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(self.url).status_code, 405)


@mock.patch("team_project.ai._call_ai_mop", return_value=None)  # テストではAIに通信しない
class ElderlyRequestFlowTests(TestCase):
    """高齢者の依頼の流れ: ホーム → 依頼作成（マイク） → 確認 → 待機"""

    def setUp(self):
        self.senior = User.objects.create_user(username="senior", password="pass")
        SeniorProfile.objects.create(user=self.senior, name="佐藤一郎", area="東京都北区")
        self.student = User.objects.create_user(username="student", password="pass")
        StudentProfile.objects.create(user=self.student, name="山田太郎", university="東洋大学")
        self.save_data = {
            "title": "電球の交換をお願いしたいです", "area": "東京都北区",
            "date": "2026-11-01", "start_time": "09:00", "end_time": "12:00",
            "text": "明日の午前中に電球を替えてほしい", "desired_time": "明日 午前中",
        }

    def test_ホームから依頼作成へ行ける(self, _):
        self.client.force_login(self.senior)
        self.assertContains(self.client.get(reverse("elderly_home")),
                            f'href="{reverse("create_request")}"')
        response = self.client.get(reverse("create_request"))
        self.assertContains(response, f'action="{reverse("confirm_request")}"')

    def test_話した内容から確認画面が作られる(self, _):
        self.client.force_login(self.senior)
        response = self.client.post(reverse("confirm_request"),
                                    {"text": "明日の午前中に電球を替えてほしい"})
        self.assertContains(response, "電球の交換をお願いしたいです")
        self.assertContains(response, 'value="東京都北区"')  # 場所はプロフィールの地域
        tomorrow = timezone.localdate() + timedelta(days=1)
        self.assertContains(response, f'value="{tomorrow.isoformat()}"')
        self.assertContains(response, 'value="09:00"')
        self.assertContains(response, f'action="{reverse("save_request")}"')

    def test_何も話していないと依頼作成に戻る(self, _):
        self.client.force_login(self.senior)
        response = self.client.post(reverse("confirm_request"), {"text": "  "})
        self.assertContains(response, "お願いしたいことを話すか、書いてください。")
        self.assertTemplateUsed(response, "elderly_request_create.html")

    def test_これでお願いすると保存されて待機画面へ(self, _):
        self.client.force_login(self.senior)
        response = self.client.post(reverse("save_request"), self.save_data)
        self.assertRedirects(response, reverse("elderly_status"))
        help_request = HelpRequest.objects.get()
        self.assertEqual(help_request.requester, self.senior)
        self.assertEqual(help_request.status, HelpRequest.Status.OPEN)
        self.assertEqual(timezone.localtime(help_request.start_at).hour, 9)
        self.assertContains(self.client.get(reverse("elderly_status")), "学生を探しています")

    def test_終わりの時間が始まりより前だと保存しない(self, _):
        self.client.force_login(self.senior)
        data = {**self.save_data, "start_time": "12:00", "end_time": "09:00"}
        response = self.client.post(reverse("save_request"), data)
        self.assertContains(response, "終わりの時間は、始まりの時間より後にしてください。")
        self.assertFalse(HelpRequest.objects.exists())

    def test_保存した依頼は学生ホームに出る(self, _):
        self.client.force_login(self.senior)
        self.client.post(reverse("save_request"), self.save_data)
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse("student_home")),
                            "電球の交換をお願いしたいです")

    def test_学生が引き受けると待機画面に学生の名前が出る(self, _):
        self.client.force_login(self.senior)
        self.client.post(reverse("save_request"), self.save_data)
        HelpRequest.objects.update(status=HelpRequest.Status.ACCEPTED, helper=self.student)
        response = self.client.get(reverse("elderly_status"))
        self.assertContains(response, "山田太郎 さん")
        self.assertContains(response, "東洋大学")

    def test_待っている依頼がなければ待機画面からホームへ(self, _):
        self.client.force_login(self.senior)
        self.assertRedirects(self.client.get(reverse("elderly_status")),
                             reverse("elderly_home"))

    def test_学生は依頼を作れない(self, _):
        self.client.force_login(self.student)
        response = self.client.post(reverse("save_request"), self.save_data, follow=True)
        self.assertRedirects(response, reverse("student_home"))
        self.assertFalse(HelpRequest.objects.exists())

    def test_ログインしていないと依頼作成は開けない(self, _):
        url = reverse("create_request")
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")


class ScheduleFromTextTests(TestCase):
    """AIがまとめた希望日時 → 確認画面の日にちと時間の初期値"""
    today = date(2026, 10, 21)

    def test_明日の午前中(self):
        self.assertEqual(_schedule_from_text("明日 午前中", self.today),
                         (date(2026, 10, 22), time(9), time(12)))

    def test_月日と時刻(self):
        self.assertEqual(_schedule_from_text("11/3（火）14時", self.today),
                         (date(2026, 11, 3), time(14), time(16)))

    def test_過ぎた日付は来年(self):
        self.assertEqual(_schedule_from_text("1月5日 午後", self.today),
                         (date(2027, 1, 5), time(13), time(17)))

    def test_読み取れないときは明日の10時から12時(self):
        self.assertEqual(_schedule_from_text("", self.today),
                         (date(2026, 10, 22), time(10), time(12)))


