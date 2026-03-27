from django.db import models


class App(models.Model):
    CATEGORY_CHOICES = [
        ('science', 'Science'),
        ('weather', 'Weather'),
        ('education', 'Education'),
        ('lifestyle', 'Lifestyle'),
        ('other', 'Other'),
    ]

    # Core
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)  # e.g. "my-uncle-the-trex"
    tagline = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    emoji = models.CharField(max_length=10, default='📱')

    # URLs
    product_url = models.URLField(blank=True, help_text='Link to the product page or website')
    app_store_url = models.URLField(blank=True)
    play_store_url = models.URLField(blank=True)
    support_email = models.EmailField(blank=True)

    # Apple/Google required pages
    support_url_notes = models.TextField(
        blank=True,
        help_text='Extra info shown on the /support/ page for this app'
    )
    privacy_policy = models.TextField(
        blank=True,
        help_text='App-specific privacy policy text (Markdown supported)'
    )

    # Display
    accent_color = models.CharField(
        max_length=20, default='#5dcaa5',
        help_text='CSS color for this app\'s accent (hex or var(...))'
    )
    is_published = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('app_detail', kwargs={'slug': self.slug})

    def get_support_url(self):
        from django.urls import reverse
        return reverse('app_support', kwargs={'slug': self.slug})

    def get_privacy_url(self):
        from django.urls import reverse
        return reverse('app_privacy', kwargs={'slug': self.slug})


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.created_at.strftime('%b %d %Y')}"
